from django.contrib.auth.decorators import user_passes_test

def grupo_requerido(*grupos):
    def check_group(user):
        if user.is_authenticated:
            return user.groups.filter(name__in=grupos).exists() or user.is_superuser
        return False
    return user_passes_test(check_group, login_url='usuarios:sesion')