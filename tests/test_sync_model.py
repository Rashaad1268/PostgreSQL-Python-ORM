from models import SyncUsers as Users, SyncPost as Post


def test_table_creation():
    Users.create_table()
    Post.create_table()


def test_model_save():
    for i in range(1, 6):
        user = Users.objects.create(name=f"Test user {i}")
        Post(name=f"test {i}", body=f"this is a test model {i}", author=user).save()


def test_model_get():
    model = Post.objects.get(1)
    mock = Post(id=1, name="test 1", body="this is a test model 1")
    assert model.id == mock.id and model.name == mock.name and model.body == mock.body


def test_model_filter():
    for _ in range(5):
        user = Users.objects.create(name="Test user created")
        Post(
            name="Test Model Created", body="this is a test model created", author=user
        ).save()

    models = Post.objects.filter(name="Test Model Created")
    assert models.count() == 5
    for model in models:
        assert (
            model.name == "Test Model Created"
            and model.body == "this is a test model created"
        )
    users = Users.objects.filter(name="Test user created")
    assert users.count() == 5
    for user in users:
        assert user.name == "Test user created"


def test_model_all():
    count1 = 1
    for post in Post.objects.all():
        assert post.id == count1
        count1 += 1

    count2 = 1
    for user in Users.objects.all():
        assert user.id == count2
        count2 += 1


def test_model_update():
    post = Post.objects.get(5)
    post.name = "The name is edited"
    post.body = "This description is edited"
    post.update()
    new_post = Post.objects.get(5)
    assert post.name == new_post.name and post.body == new_post.body

    user = Users.objects.get(3)
    user.name = "This username is edited"
    user.update()
    assert user.name == Users.objects.get(3).name


def test_model_delete():
    model = Post.objects.get(7)
    model.delete()
    assert Post.objects.get(7) is None

    user = Users.objects.get(2)
    user.delete()
    assert Users.objects.get(2) is None


def test_model_comparison():
    post1 = Post.objects.get(1)
    post2 = Post.objects.get(2)

    assert post1 == post1
    assert post2 == post2
    assert post1 != post2

    user1 = Users.objects.get(1)
    user2 = Users.objects.get(3)

    assert user1 == user1
    assert user2 == user2
    assert user1 != user2


def test_model_hash():
    post = Post.objects.get(1)
    assert hash(post) == post.id

    user = Users.objects.get(1)
    assert hash(user) == user.id


def test_model_create():
    post = Post.objects.create(
        name="Test post created by Model.objects.create", body="test post create", author=1
    )
    assert (
        post.name == "Test post created by Model.objects.create"
        and post.body == "test post create"
    )

    user = Users.objects.create(name="Test user created by Model.objects.create")
    assert user.name == "Test user created by Model.objects.create"


def test_model_drop():
    Post.drop(delete_migration_files=False)
    Users.drop(delete_migration_files=False)
