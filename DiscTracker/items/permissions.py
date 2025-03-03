def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def is_in_group(user, group_name):
    return user.is_authenticated and user.groups.filter(name=group_name).exists()
