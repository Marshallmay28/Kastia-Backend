from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from api.models import Market, AuditLog
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Setup system roles and permissions'

    def handle(self, *args, **options):
        # 1. Market Operations
        market_ops, _ = Group.objects.get_or_create(name='Market Operations')
        
        # Get ContentTypes
        market_ct = ContentType.objects.get_for_model(Market)
        
        # Define permissions for Market Ops
        market_ops_perms = [
            'add_market',
            'change_market',
            'delete_market',
            'can_seed_liquidity',
            'can_resolve_market',
        ]
        
        for codename in market_ops_perms:
            try:
                perm = Permission.objects.get(codename=codename, content_type=market_ct)
                market_ops.permissions.add(perm)
                self.stdout.write(self.style.SUCCESS(f'Added {codename} to Market Operations'))
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Permission {codename} not found'))

        # 2. Compliance
        compliance, _ = Group.objects.get_or_create(name='Compliance')
        compliance_perms = [
            'can_halt_trading',
            'view_market',
        ]
        for codename in compliance_perms:
             try:
                perm = Permission.objects.get(codename=codename, content_type=market_ct)
                compliance.permissions.add(perm)
                self.stdout.write(self.style.SUCCESS(f'Added {codename} to Compliance'))
             except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Permission {codename} not found'))
        
        # Audit Log permissions for compliance
        audit_ct = ContentType.objects.get_for_model(AuditLog)
        view_audit = Permission.objects.get(codename='view_auditlog', content_type=audit_ct)
        compliance.permissions.add(view_audit)


        # 3. Support
        support, _ = Group.objects.get_or_create(name='Customer Support')
        user_ct = ContentType.objects.get_for_model(User)
        support_perms = ['view_user']
        # Note: change_password is not a standard permission, usually handled via logic
        
        for codename in support_perms:
             try:
                perm = Permission.objects.get(codename=codename, content_type=user_ct)
                support.permissions.add(perm)
                self.stdout.write(self.style.SUCCESS(f'Added {codename} to Support'))
             except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Permission {codename} not found'))

        self.stdout.write(self.style.SUCCESS('Successfully configured roles.'))
