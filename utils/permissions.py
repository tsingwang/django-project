from rest_framework import exceptions
from rest_framework import permissions

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


class ActionModelPermissions(permissions.DjangoModelPermissions):

    def get_required_action_permissions(self, view, model_cls):
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }

        if not getattr(view, 'action_model_perms_map', None) or \
                view.action not in view.action_model_perms_map:
            raise exceptions.MethodNotAllowed(view.action)

        return [perm % kwargs for perm in view.action_model_perms_map[view.action]]

    def has_permission(self, request, view):
        # Workaround to ensure DjangoModelPermissions are not applied
        # to the root view when using DefaultRouter.
        if getattr(view, '_ignore_model_permissions', False):
            return True

        if not request.user or (
           not request.user.is_authenticated and self.authenticated_users_only):
            return False

        queryset = self._queryset(view)
        try:
            # Try looking if any perms are set for current action first.
            perms = self.get_required_action_permissions(view, queryset.model)
        except exceptions.MethodNotAllowed:
            perms = self.get_required_permissions(request.method, queryset.model)

        return request.user.has_perms(perms)


class ActionModelWithReadPermissions(ActionModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class ActionObjectPermissions(ActionModelPermissions):

    def get_required_action_object_permissions(self, view, model_cls):
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name': model_cls._meta.model_name
        }

        if not getattr(view, 'action_object_perms_map', None) or \
                view.action not in view.action_object_perms_map:
            raise exceptions.MethodNotAllowed(view.action)

        return [perm % kwargs for perm in view.action_object_perms_map[view.action]]

    def has_object_permission(self, request, view, obj):
        # authentication checks have already executed via has_permission
        queryset = self._queryset(view)
        model_cls = queryset.model
        user = request.user

        try:
            # Try looking if any perms are set for current action first.
            perms = self.get_required_action_object_permissions(view, queryset.model)
        except exceptions.MethodNotAllowed:
            perms = self.get_required_permissions(request.method, model_cls)

        if not user.has_perms(perms, obj):
            # If the user does not have permissions we need to determine if
            # they have read permissions to see 403, or not, and simply see
            # a 404 response.

            if request.method in SAFE_METHODS:
                # Read permissions already checked and failed, no need
                # to make another lookup.
                raise Http404

            read_perms = self.get_required_permissions('GET', model_cls)
            if not user.has_perms(read_perms, obj):
                raise Http404

            # Has read permissions.
            return False

        return True


class ActionObjectWithReadPermissions(ActionObjectPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }
