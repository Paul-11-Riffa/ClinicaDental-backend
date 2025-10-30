from dental_clinic_backend.admin_sites import public_admin_site

print("Modelos registrados en public_admin_site:")
for model in public_admin_site._registry:
    print(f"  - {model._meta.app_label}.{model.__name__}")
