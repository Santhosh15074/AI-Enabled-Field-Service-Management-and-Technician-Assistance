import pytest
from sqlalchemy import select

from app.models import ComplaintCategory, KnowledgeBaseEntry, Role
from tests.conftest import log_in


@pytest.fixture
def admin(make_user):
    return make_user(Role.ADMIN)


@pytest.fixture
def technician(make_user):
    return make_user(Role.TECHNICIAN)


@pytest.fixture
def category(db_session):
    # The seed migration already adds Electrical, Mechanical, etc.; a fresh one keeps these
    # tests independent of that seed data.
    category = ComplaintCategory(category_name="Test category", urgency_level="medium")
    db_session.add(category)
    db_session.commit()
    return category


ENTRY = {"equipment_type": "Pump", "issue_pattern": "The pump is leaking", "suggested_fix": "Tighten the fitting."}


class TestListEntries:
    def test_admin_sees_every_entry_with_its_category_name(self, client, db_session, admin, category):
        db_session.add(KnowledgeBaseEntry(category_id=category.id, **ENTRY))
        db_session.commit()

        log_in(client, admin.email)
        response = client.get("/api/knowledge-base")

        assert response.status_code == 200
        matches = [row for row in response.json() if row["issue_pattern"] == "The pump is leaking"]
        assert matches[0]["category_name"] == "Test category"

    def test_only_admins_can_list_entries(self, client, technician):
        log_in(client, technician.email)

        assert client.get("/api/knowledge-base").status_code == 403


class TestCreateEntry:
    def test_admin_can_create_an_entry(self, client, db_session, admin, category):
        log_in(client, admin.email)

        response = client.post("/api/knowledge-base", json={"category_id": category.id, **ENTRY})

        assert response.status_code == 201
        assert response.json()["category_name"] == "Test category"
        assert db_session.scalar(select(KnowledgeBaseEntry).where(KnowledgeBaseEntry.issue_pattern == ENTRY["issue_pattern"]))

    def test_rejects_an_unknown_category(self, client, admin):
        log_in(client, admin.email)

        response = client.post("/api/knowledge-base", json={"category_id": 999999, **ENTRY})

        assert response.status_code == 400

    def test_rejects_a_blank_fix(self, client, admin, category):
        log_in(client, admin.email)

        response = client.post("/api/knowledge-base", json={"category_id": category.id, **ENTRY, "suggested_fix": "   "})

        assert response.status_code == 400

    def test_only_admins_can_create_entries(self, client, technician, category):
        log_in(client, technician.email)

        assert client.post("/api/knowledge-base", json={"category_id": category.id, **ENTRY}).status_code == 403


class TestUpdateEntry:
    @pytest.fixture
    def entry_id(self, db_session, category):
        entry = KnowledgeBaseEntry(category_id=category.id, **ENTRY)
        db_session.add(entry)
        db_session.commit()
        return entry.id

    def test_admin_can_update_an_entry(self, client, db_session, admin, category, entry_id):
        log_in(client, admin.email)

        response = client.patch(
            f"/api/knowledge-base/{entry_id}",
            json={"category_id": category.id, "equipment_type": "Pump", "issue_pattern": "Updated issue", "suggested_fix": "Updated fix"},
        )

        assert response.status_code == 200
        assert response.json()["issue_pattern"] == "Updated issue"
        updated = db_session.get(KnowledgeBaseEntry, entry_id)
        db_session.refresh(updated)
        assert updated.suggested_fix == "Updated fix"

    def test_rejects_blanking_the_issue(self, client, admin, category, entry_id):
        log_in(client, admin.email)

        response = client.patch(f"/api/knowledge-base/{entry_id}", json={"category_id": category.id, **ENTRY, "issue_pattern": "  "})

        assert response.status_code == 400

    def test_updating_an_unknown_entry_is_404(self, client, admin, category):
        log_in(client, admin.email)

        response = client.patch("/api/knowledge-base/999999", json={"category_id": category.id, **ENTRY})

        assert response.status_code == 404

    def test_only_admins_can_update_entries(self, client, technician, category, entry_id):
        log_in(client, technician.email)

        response = client.patch(f"/api/knowledge-base/{entry_id}", json={"category_id": category.id, **ENTRY})

        assert response.status_code == 403


class TestDeleteEntry:
    @pytest.fixture
    def entry_id(self, db_session, category):
        entry = KnowledgeBaseEntry(category_id=category.id, **ENTRY)
        db_session.add(entry)
        db_session.commit()
        return entry.id

    def test_admin_can_delete_an_entry(self, client, db_session, admin, entry_id):
        log_in(client, admin.email)

        response = client.delete(f"/api/knowledge-base/{entry_id}")

        assert response.status_code == 204
        assert db_session.get(KnowledgeBaseEntry, entry_id) is None

    def test_deleting_an_unknown_entry_is_404(self, client, admin):
        log_in(client, admin.email)

        assert client.delete("/api/knowledge-base/999999").status_code == 404

    def test_only_admins_can_delete_entries(self, client, technician, entry_id):
        log_in(client, technician.email)

        assert client.delete(f"/api/knowledge-base/{entry_id}").status_code == 403
