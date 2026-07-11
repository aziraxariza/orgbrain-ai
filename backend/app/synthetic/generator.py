"""FR-701: Generate Synthetic Organization Data.

Produces a plausible org: reporting hierarchy (exec -> managers -> ICs), teams,
skills, projects with staggered start/target dates, tasks with dependency chains
inside each project, realistic P0-P3 priority mix, and some intentionally
overloaded employees / drifted tasks so every risk detector has something to find.
"""
import random
import uuid
from datetime import date, timedelta

from faker import Faker
from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.team import Team, TeamMembership
from app.models.project import Project, ProjectStatus
from app.models.task import Task, TaskPriority, TaskStatus
from app.core.security import hash_password
from app.config import settings

fake = Faker()

SKILL_POOL = [
    "python", "react", "sql", "kubernetes", "figma", "product-strategy",
    "sales", "recruiting", "finance-modeling", "aws", "typescript",
    "data-analysis", "project-management", "ml-engineering", "devops",
]

ROLE_LEVELS = [
    ("VP", 1), ("Director", 2), ("Senior Manager", 3), ("Manager", 4),
    ("Senior Engineer", 5), ("Engineer", 5), ("Analyst", 5), ("Associate", 5),
]


def _random_skills() -> list[str]:
    return random.sample(SKILL_POOL, k=random.randint(2, 4))


def generate_organization(
    db: Session,
    org_name: str = "Acme Demo Corp",
    admin_email: str = "admin@acmedemo.com",
    admin_password: str = "password123",
    n_employees: int | None = None,
    n_projects: int | None = None,
    n_tasks: int | None = None,
) -> Organization:
    n_employees = n_employees or settings.synthetic_employees
    n_projects = n_projects or settings.synthetic_projects
    n_tasks = n_tasks or settings.synthetic_tasks

    org = Organization(name=org_name, slug="-".join(org_name.lower().split()))
    db.add(org)
    db.flush()

    db.add(User(
        tenant_id=org.organization_id, email=admin_email,
        hashed_password=hash_password(admin_password),
        full_name="Demo Admin", role=UserRole.ADMIN,
    ))

    # --- Employees: build a shallow hierarchy so reports_to edges form a real tree ---
    employees: list[Employee] = []
    exec_emp = Employee(
        tenant_id=org.organization_id, name=fake.name(), role="CEO",
        manager_id=None, skills=_random_skills(),
        available_hours_per_week=40, current_workload_hours=0,
        is_active=True, hire_date=fake.date_between(start_date="-6y", end_date="-3y"),
    )
    db.add(exec_emp)
    db.flush()
    employees.append(exec_emp)

    remaining = n_employees - 1
    # Distribute the rest across a few management layers, each employee assigned
    # a manager already created (guarantees an acyclic tree).
    layer_managers = [exec_emp]
    while remaining > 0:
        next_layer = []
        layer_size = min(remaining, max(len(layer_managers) * random.randint(3, 6), 5))
        for _ in range(layer_size):
            manager = random.choice(layer_managers)
            role, _ = random.choice(ROLE_LEVELS)
            overloaded = random.random() < 0.12  # seed some intentional capacity violations
            emp = Employee(
                tenant_id=org.organization_id, name=fake.name(), role=role,
                manager_id=manager.employee_id, skills=_random_skills(),
                available_hours_per_week=40 if not overloaded else random.choice([20, 25, 30]),
                current_workload_hours=0, is_active=True,
                hire_date=fake.date_between(start_date="-5y", end_date="-1m"),
            )
            db.add(emp)
            next_layer.append(emp)
        db.flush()
        employees.extend(next_layer)
        layer_managers = next_layer if next_layer else layer_managers
        remaining -= layer_size

    # --- Teams ---
    n_teams = max(n_projects // 3, 5)
    teams = []
    for _ in range(n_teams):
        lead = random.choice(employees)
        team = Team(tenant_id=org.organization_id, name=f"{fake.word().capitalize()} Team", lead_employee_id=lead.employee_id)
        db.add(team)
        teams.append(team)
    db.flush()
    for emp in employees:
        team = random.choice(teams)
        db.add(TeamMembership(tenant_id=org.organization_id, team_id=team.team_id, employee_id=emp.employee_id))

    # --- Projects ---
    projects = []
    for _ in range(n_projects):
        start = fake.date_between(start_date="-4mo", end_date="-1mo")
        target = start + timedelta(days=random.randint(30, 150))
        status = random.choices(
            [ProjectStatus.ACTIVE, ProjectStatus.AT_RISK, ProjectStatus.PLANNED, ProjectStatus.COMPLETED],
            weights=[0.5, 0.2, 0.15, 0.15],
        )[0]
        project = Project(
            tenant_id=org.organization_id, name=f"{fake.catch_phrase()}",
            description=fake.sentence(nb_words=12), start_date=start,
            target_end_date=target, status=status,
        )
        db.add(project)
        projects.append(project)
    db.flush()

    # --- Tasks (with dependency chains per project) ---
    tasks_per_project = max(n_tasks // n_projects, 4)
    all_tasks: list[Task] = []
    for project in projects:
        chain: list[Task] = []
        cursor = project.start_date
        for i in range(tasks_per_project):
            duration_days = random.randint(3, 14)
            est_hours = duration_days * random.uniform(4, 8)
            assignee = random.choice(employees)
            progress = 0.0
            actual_hours = 0.0
            status = TaskStatus.TODO

            if project.status in (ProjectStatus.ACTIVE, ProjectStatus.AT_RISK, ProjectStatus.COMPLETED):
                if project.status == ProjectStatus.COMPLETED or i < tasks_per_project * 0.6:
                    status = TaskStatus.DONE if random.random() < 0.7 else TaskStatus.IN_PROGRESS
                if status == TaskStatus.DONE:
                    progress = 100.0
                    actual_hours = est_hours * random.uniform(0.9, 1.3)
                elif status == TaskStatus.IN_PROGRESS:
                    # Intentionally drift some tasks behind schedule for FR-301 to catch.
                    drifted = random.random() < 0.25
                    progress = random.uniform(5, 30) if drifted else random.uniform(30, 70)
                    actual_hours = est_hours * (progress / 100)

            task = Task(
                tenant_id=org.organization_id, project_id=project.project_id,
                name=f"{fake.bs().capitalize()}", assigned_person_id=assignee.employee_id,
                estimated_hours=round(est_hours, 1), actual_hours_completed=round(actual_hours, 1),
                progress_percent=round(progress, 1), start_date=cursor,
                deadline=cursor + timedelta(days=duration_days),
                priority=random.choices(list(TaskPriority), weights=[0.1, 0.3, 0.4, 0.2])[0],
                status=status,
            )
            db.add(task)
            chain.append(task)
            all_tasks.append(task)
            cursor = cursor + timedelta(days=max(duration_days // 2, 1))
        db.flush()

        # Chain each task to depend on the previous 1-2 tasks in the same project,
        # giving the graph real depends_on edges for critical-path/Monte Carlo.
        for i in range(1, len(chain)):
            n_deps = 1 if i < 2 else random.randint(1, 2)
            for dep in chain[max(0, i - n_deps):i]:
                chain[i].depends_on.append(dep)

    db.commit()
    return org
