from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select
from starlette.requests import Request

from hans.core.auth import User, hash_password, verify_password
from hans.core.db import SessionLocal, engine
from hans.core.settings import settings
from hans.instruments import Instrument, Workstation
from hans.orders import Order, Result, ServiceRun, Specimen, TestRun
from hans.owners import Owner
from hans.patients import Patient, Species
from hans.services import ServiceCatalog
from hans.specimens import SpecimenType
from hans.tests import TestCatalog
from hans.tubes import TubeType


# --- Auth -------------------------------------------------------------

class AdminAuth(AuthenticationBackend):
    # Use session storage to track authenticated admins.
    async def login(self, request: Request) -> bool:
        # Read submitted credentials from the login form.
        form = await request.form()
        username = str(form.get("username") or "")
        password = str(form.get("password") or "")
        if not username or not password:
            return False

        # Load the user and validate admin role + password.
        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
        if not user or user.role != "admin":
            return False
        if not verify_password(password, user.hashed_password):
            return False

        # Persist admin identity in the session.
        request.session["admin_user"] = user.id
        return True

    # Check each request using the session user id.
    async def authenticate(self, request: Request) -> bool:
        user_id = request.session.get("admin_user")
        if not user_id:
            return False

        # Validate the session user is still an admin.
        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
        if not user or user.role != "admin":
            return False
        return True

    # Clear the session during logout.
    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True


# --- Views ------------------------------------------------------------
# ModelView declarations for the admin console.

class UserAdmin(ModelView, model=User):
    # Hide hashed passwords in list and details.
    column_exclude_list = [User.hashed_password]
    column_labels = {"hashed_password": "password"}
    form_create_rules = ["username", "email", "role", "hashed_password"]
    form_edit_rules = ["username", "email", "role"]

    # Hash the password only on create.
    async def on_model_change(
        self,
        data: dict,
        model: User,
        is_created: bool,
        request: Request,
    ) -> None:
        if is_created:
            raw_password = str(data.get("hashed_password") or "")
            if not raw_password:
                raise ValueError("Password is required")
            data["hashed_password"] = hash_password(raw_password)


class OwnerAdmin(ModelView, model=Owner):
    column_list = [
        Owner.id,
        Owner.first_name,
        Owner.last_name,
        Owner.email,
        Owner.phone,
        Owner.comment,
    ]


class PatientAdmin(ModelView, model=Patient):
    column_list = [
        Patient.id,
        Patient.name,
        Patient.species,
        Patient.owner_id,
        Patient.breed,
        Patient.birth_date,
        Patient.created_at,
        Patient.comment,
    ]
    # Show owner name instead of raw ID.
    column_labels = {"owner_id": "owner"}
    column_formatters = {
        "owner_id": lambda model, attr: (
            f"{getattr(model.owner, 'first_name', '')} "
            f"{getattr(model.owner, 'last_name', '')}"
        ).strip(),
    }


class SpeciesAdmin(ModelView, model=Species):
    name = "Specie"
    name_plural = "Species"
    column_list = [
        Species.id,
        Species.code,
        Species.name,
        Species.latin_name,
        Species.active,
    ]


class OrderAdmin(ModelView, model=Order):
    column_list = [
        Order.id,
        Order.patient_id,
        Order.created_by,
        Order.created_at,
        Order.archived,
        Order.comment,
    ]
    # Show related patient and creator details.
    column_labels = {"patient_id": "patient", "created_by": "created by"}
    column_formatters = {
        "patient_id": lambda model, attr: getattr(model.patient, "name", ""),
        "created_by": lambda model, attr: getattr(model.creator, "username", ""),
    }


class SpecimenAdmin(ModelView, model=Specimen):
    column_list = [
        Specimen.specimen_id,
        Specimen.order_id,
        Specimen.specimen_type_id,
        Specimen.status,
        Specimen.collected_at,
        Specimen.received_at,
    ]
    # Render specimen type code instead of raw ID.
    column_labels = {"specimen_type_id": "specimen type"}
    column_formatters = {
        "specimen_type_id": lambda model, attr: getattr(model.specimen_type, "code", ""),
    }


class TestRunAdmin(ModelView, model=TestRun):
    column_list = [
        TestRun.id,
        TestRun.order_id,
        TestRun.test_catalog_id,
        TestRun.specimen_id,
        TestRun.workstation_id,
        TestRun.instrument_id,
        TestRun.status,
        TestRun.price,
    ]
    # Show related test, workstation, and instrument values.
    column_labels = {
        "test_catalog_id": "test",
        "workstation_id": "workstation",
        "instrument_id": "instrument",
    }
    column_formatters = {
        "test_catalog_id": lambda model, attr: getattr(model.test_catalog, "code", ""),
        "workstation_id": lambda model, attr: getattr(model.workstation, "name", ""),
        "instrument_id": lambda model, attr: getattr(model.instrument, "code", ""),
    }


class ResultAdmin(ModelView, model=Result):
    column_list = [
        Result.id,
        Result.test_run_id,
        Result.value,
        Result.units,
        Result.flags,
        Result.completed_at,
        Result.verified,
    ]


class ServiceRunAdmin(ModelView, model=ServiceRun):
    column_list = [
        ServiceRun.id,
        ServiceRun.order_id,
        ServiceRun.service_catalog_id,
        ServiceRun.status,
        ServiceRun.price,
        ServiceRun.completed_at,
    ]
    # Show service name instead of raw ID.
    column_labels = {"service_catalog_id": "service"}
    column_formatters = {
        "service_catalog_id": lambda model, attr: getattr(model.service_catalog, "name", ""),
    }


class TestCatalogAdmin(ModelView, model=TestCatalog):
    name = "Test in Test Catalog"
    name_plural = "Test Catalog"

    # Use relationship field to show a specimen type dropdown.
    form_create_rules = ["code", "description", "price", "specimen_type"]
    form_edit_rules = ["code", "description", "price", "specimen_type"]

    column_list = [
        TestCatalog.code,
        TestCatalog.description,
        TestCatalog.price,
        TestCatalog.specimen_type_id,
    ]
    # Use friendly column headers.
    column_labels = {"specimen_type_id": "specimen type"}
    # Render specimen type code instead of raw ID.
    column_formatters = {
        "specimen_type_id": lambda model, attr: getattr(model.specimen_type, "code", ""),
    }


class ServiceCatalogAdmin(ModelView, model=ServiceCatalog):
    name = "Service in Service Catalog"
    name_plural = "Service Catalog"
    column_list = [
        ServiceCatalog.id,
        ServiceCatalog.name,
        ServiceCatalog.description,
        ServiceCatalog.price,
    ]


class SpecimenTypeAdmin(ModelView, model=SpecimenType):
    column_list = [
        SpecimenType.id,
        SpecimenType.code,
        SpecimenType.name,
        SpecimenType.type,
        SpecimenType.tube_type_id,
        SpecimenType.description,
    ]
    # Show tube type code instead of raw ID.
    column_labels = {"tube_type_id": "tube type"}
    column_formatters = {
        "tube_type_id": lambda model, attr: getattr(model.tube_type, "code", ""),
    }


class TubeTypeAdmin(ModelView, model=TubeType):
    column_list = [
        TubeType.id,
        TubeType.code,
        TubeType.name,
        TubeType.description,
    ]


class InstrumentAdmin(ModelView, model=Instrument):
    column_list = [
        Instrument.id,
        Instrument.code,
        Instrument.name,
        Instrument.model,
        Instrument.location,
    ]


class WorkstationAdmin(ModelView, model=Workstation):
    column_list = [
        Workstation.id,
        Workstation.name,
        Workstation.instrument_id,
    ]
    # Show instrument code instead of raw ID.
    column_labels = {"instrument_id": "instrument"}
    column_formatters = {
        "instrument_id": lambda model, attr: getattr(model.instrument, "code", ""),
    }


# --- Init -------------------------------------------------------------

def build_admin(app: FastAPI) -> Admin:
    # Attach SQLAdmin to the FastAPI app at /admin.
    auth_backend = AdminAuth(secret_key=settings.secret_key)
    admin = Admin(app, engine, authentication_backend=auth_backend, base_url="/admin")
    admin.add_view(UserAdmin)
    admin.add_view(OwnerAdmin)
    admin.add_view(PatientAdmin)
    admin.add_view(SpeciesAdmin)

    admin.add_view(OrderAdmin)
    admin.add_view(SpecimenAdmin)
    admin.add_view(TestRunAdmin)
    admin.add_view(ResultAdmin)

    admin.add_view(ServiceRunAdmin)

    admin.add_view(TestCatalogAdmin)
    admin.add_view(ServiceCatalogAdmin)
    admin.add_view(SpecimenTypeAdmin)
    admin.add_view(TubeTypeAdmin)

    admin.add_view(InstrumentAdmin)
    admin.add_view(WorkstationAdmin)

    return admin
