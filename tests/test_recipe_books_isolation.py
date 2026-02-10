"""Tests verifying recipe book file storage is isolated to temp dirs during testing,
and that the seed script module is importable and has expected interface."""

import io
import os


def test_recipe_upload_does_not_pollute_data_dir(authed_client):
    """Uploading a recipe book in tests must NOT create files in data/recipe_books/."""
    real_data_dir = os.path.join(os.getcwd(), "data", "recipe_books")
    before = set(os.listdir(real_data_dir)) if os.path.isdir(real_data_dir) else set()

    content = b"# Test Recipe\nThis is a test recipe."
    files = {"file": ("test_recipe.md", io.BytesIO(content), "text/markdown")}
    resp = authed_client.post("/recipes/books", files=files, data={"title": "Test"})
    assert resp.status_code == 201

    after = set(os.listdir(real_data_dir)) if os.path.isdir(real_data_dir) else set()
    new_files = after - before
    assert not new_files, f"Test leaked files to data/recipe_books/: {new_files}"


def test_recipe_repo_uses_configurable_data_dir():
    """RecipeRepo accepts a custom data_dir parameter."""
    from app.repos.recipe_repo import RecipeRepo, DATA_DIR

    default_repo = RecipeRepo()
    assert default_repo._data_dir == DATA_DIR

    custom_repo = RecipeRepo(data_dir="/tmp/custom_recipes")
    assert custom_repo._data_dir == "/tmp/custom_recipes"


def test_seed_script_is_importable():
    """The seed script module can be imported and has the expected interface."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "seed_wikibooks_cookbook",
        os.path.join(os.getcwd(), "scripts", "seed_wikibooks_cookbook.py"),
    )
    assert spec is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "seed")
    assert hasattr(mod, "slugify")
    assert mod.slugify("Apple Pie Recipe!") == "apple_pie_recipe"
