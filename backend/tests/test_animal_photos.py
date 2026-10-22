"""``POST/DELETE /animals/{id}/photo`` and the ``photo_url`` field."""

from __future__ import annotations

import pytest

from app.uploads import ANIMAL_PHOTO_DIR, MAX_PHOTO_BYTES

# Smallest byte strings that pass the format check -- the API only looks at
# the first bytes, it never decodes the image.
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 100


def upload(client, animal_id, headers, content=JPEG, name="photo.jpg", mime="image/jpeg"):
    return client.post(
        f"/animals/{animal_id}/photo",
        files={"file": (name, content, mime)},
        headers=headers,
    )


def stored_file(photo_url: str):
    return ANIMAL_PHOTO_DIR / photo_url.rsplit("/", 1)[-1]


def test_new_animal_has_no_photo(client, animal_id):
    assert client.get(f"/animals/{animal_id}").json()["photo_url"] is None


@pytest.mark.parametrize(
    ("content", "name", "extension"),
    [(JPEG, "a.jpg", ".jpg"), (PNG, "a.png", ".png"), (WEBP, "a.webp", ".webp")],
)
def test_upload_accepts_jpeg_png_and_webp(client, staff_headers, animal_id, content, name, extension):
    response = upload(client, animal_id, staff_headers, content=content, name=name)

    assert response.status_code == 200, response.text
    photo_url = response.json()["photo_url"]
    assert photo_url.startswith(f"/uploads/animals/{animal_id}-")
    assert photo_url.endswith(extension)


def test_photo_url_appears_in_list_and_detail_and_is_served(client, staff_headers, animal_id):
    photo_url = upload(client, animal_id, staff_headers).json()["photo_url"]

    assert client.get(f"/animals/{animal_id}").json()["photo_url"] == photo_url
    assert client.get("/animals").json()[0]["photo_url"] == photo_url
    served = client.get(photo_url)
    assert served.status_code == 200
    assert served.content == JPEG


def test_user_file_name_is_not_used(client, staff_headers, animal_id):
    photo_url = upload(client, animal_id, staff_headers, name="../../evil.jpg").json()["photo_url"]

    assert "evil" not in photo_url
    assert stored_file(photo_url).parent == ANIMAL_PHOTO_DIR


def test_reupload_replaces_and_removes_the_old_file(client, staff_headers, animal_id):
    first = upload(client, animal_id, staff_headers).json()["photo_url"]
    second = upload(client, animal_id, staff_headers, content=PNG, name="b.png").json()["photo_url"]

    assert first != second
    assert not stored_file(first).exists()
    assert stored_file(second).exists()


def test_delete_clears_the_photo_and_the_file(client, staff_headers, animal_id):
    photo_url = upload(client, animal_id, staff_headers).json()["photo_url"]

    response = client.delete(f"/animals/{animal_id}/photo", headers=staff_headers)

    assert response.status_code == 200
    assert response.json()["photo_url"] is None
    assert not stored_file(photo_url).exists()


def test_delete_without_a_photo_is_fine(client, staff_headers, animal_id):
    response = client.delete(f"/animals/{animal_id}/photo", headers=staff_headers)

    assert response.status_code == 200
    assert response.json()["photo_url"] is None


def test_unknown_animal_is_404(client, staff_headers):
    assert upload(client, 999, staff_headers).status_code == 404
    assert client.delete("/animals/999/photo", headers=staff_headers).status_code == 404


def test_text_file_renamed_to_jpg_is_415(client, staff_headers, animal_id):
    response = upload(client, animal_id, staff_headers, content=b"just some text", name="fake.jpg")

    assert response.status_code == 415
    assert isinstance(response.json()["detail"], str)
    assert client.get(f"/animals/{animal_id}").json()["photo_url"] is None


def test_file_over_5_mb_is_413_and_nothing_is_kept(client, staff_headers, animal_id):
    before = set(ANIMAL_PHOTO_DIR.iterdir())
    too_big = JPEG + b"\x00" * (MAX_PHOTO_BYTES + 1 - len(JPEG))

    response = upload(client, animal_id, staff_headers, content=too_big)

    assert response.status_code == 413
    assert isinstance(response.json()["detail"], str)
    assert set(ANIMAL_PHOTO_DIR.iterdir()) == before
    assert client.get(f"/animals/{animal_id}").json()["photo_url"] is None


def test_file_of_exactly_5_mb_is_accepted(client, staff_headers, animal_id):
    exact = JPEG + b"\x00" * (MAX_PHOTO_BYTES - len(JPEG))

    assert upload(client, animal_id, staff_headers, content=exact).status_code == 200


def test_photo_routes_need_a_token(client, animal_id):
    assert upload(client, animal_id, {}).status_code == 401
    assert client.delete(f"/animals/{animal_id}/photo").status_code == 401


def test_photo_routes_are_staff_only(client, adopter_headers, animal_id):
    assert upload(client, animal_id, adopter_headers).status_code == 403
    assert client.delete(f"/animals/{animal_id}/photo", headers=adopter_headers).status_code == 403


def test_photo_url_cannot_be_sent_to_create_or_update(client, staff_headers, shelter_id, animal_id):
    created = client.post(
        "/animals",
        json={
            "name": "Mia",
            "species": "cat",
            "breed": "tabby",
            "age": 2,
            "shelter_id": shelter_id,
            "photo_url": "/uploads/animals/x.jpg",
        },
        headers=staff_headers,
    )
    patched = client.patch(
        f"/animals/{animal_id}",
        json={"photo_url": "/uploads/animals/x.jpg"},
        headers=staff_headers,
    )

    assert created.status_code == 422
    assert patched.status_code == 422
