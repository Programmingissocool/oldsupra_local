from decimal import Decimal

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Account, TestCustomer, UserProfile


TEST_CUSTOMER_USERNAME = 'oldsupra_test_customer'
TEST_CUSTOMER_EMAIL = 'animamucharashvili+oldsupra-test@gmail.com'
TEST_CUSTOMER_EXTRA_EMAILS = ['guka.gurgenidze@gmail.com']


class AccountAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'last_login', 'date_joined', 'is_active', 'is_staff', 'is_superadmin', 'is_admin',)
    list_display_links = ('email', 'first_name', 'last_name')
    list_editable = ('is_active', 'is_admin', 'is_superadmin',)
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ('email', 'first_name', 'last_name',)
    fieldsets = ()


class TestCustomerAdmin(admin.ModelAdmin):
    fields = ('first_name', 'last_name', 'email', 'phone_number', 'is_active', 'date_joined', 'last_login')
    list_display = ('email', 'full_name_display', 'phone_number', 'is_active', 'test_actions')
    readonly_fields = ('date_joined', 'last_login')
    list_display_links = ('email',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(username=TEST_CUSTOMER_USERNAME)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'create-test-customer/',
                self.admin_site.admin_view(self.create_test_customer),
                name='accounts_testcustomer_create_customer',
            ),
            path(
                '<path:object_id>/send-test-order/',
                self.admin_site.admin_view(self.send_test_order),
                name='accounts_testcustomer_send_order',
            ),
        ]
        return custom_urls + urls

    def has_add_permission(self, request):
        return not TestCustomer.objects.filter(username=TEST_CUSTOMER_USERNAME).exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def add_view(self, request, form_url='', extra_context=None):
        return self.create_test_customer(request)

    def save_model(self, request, obj, form, change):
        obj.username = TEST_CUSTOMER_USERNAME
        obj.is_admin = False
        obj.is_staff = False
        obj.is_superadmin = False
        super().save_model(request, obj, form, change)

    def full_name_display(self, obj):
        return obj.full_name()
    full_name_display.short_description = 'Name'

    def test_actions(self, obj):
        send_url = reverse('admin:accounts_testcustomer_send_order', args=[obj.pk])
        return format_html('<a class="button" href="{}">Create test order and send email</a>', send_url)
    test_actions.short_description = 'Actions'

    def _available_test_email(self):
        local_part, domain = TEST_CUSTOMER_EMAIL.split('@', 1)
        for index in range(1, 1000):
            email = TEST_CUSTOMER_EMAIL if index == 1 else '{}-{}@{}'.format(local_part, index, domain)
            if not Account.objects.filter(email=email).exists():
                return email
        raise IntegrityError('Could not find an unused pretend customer email address.')

    def _get_or_create_test_customer(self):
        customer = TestCustomer.objects.filter(username=TEST_CUSTOMER_USERNAME).first()
        if customer:
            return customer, False

        customer = TestCustomer(
            username=TEST_CUSTOMER_USERNAME,
            email=self._available_test_email(),
            first_name='Pretend',
            last_name='Customer',
            phone_number='+995555000000',
            is_active=False,
            is_staff=False,
            is_admin=False,
            is_superadmin=False,
        )
        customer.set_unusable_password()
        customer.save()
        return customer, True

    def create_test_customer(self, request):
        try:
            customer, created = self._get_or_create_test_customer()
        except Exception as exc:
            self.message_user(request, 'Pretend customer could not be created: {}'.format(exc), level='ERROR')
            return HttpResponseRedirect(reverse('admin:accounts_testcustomer_changelist'))

        if created:
            self.message_user(request, 'Pretend customer created. Emails will be sent to {}.'.format(customer.email))
        else:
            self.message_user(request, 'Pretend customer already exists. Emails will be sent to {}.'.format(customer.email))
        return HttpResponseRedirect(reverse('admin:accounts_testcustomer_changelist'))

    def send_test_order(self, request, object_id):
        from carts.views import _send_customer_order_email
        from orders.models import Order, OrderProduct, Payment
        from shop.models import Product, Variation

        customer = self.get_object(request, object_id)
        if customer is None:
            customer, _ = self._get_or_create_test_customer()

        product = Product.objects.filter(is_availiable=True).order_by('id').first() or Product.objects.order_by('id').first()
        if product is None:
            self.message_user(request, 'Cannot create a test order because there are no products.', level='ERROR')
            return HttpResponseRedirect(reverse('admin:accounts_testcustomer_changelist'))

        variation = Variation.objects.filter(product=product).select_related('color', 'size').order_by('id').first()
        unit_price = Decimal(str(variation.get_price if variation else product.get_price()))
        shipping = Decimal('0.00')
        total = unit_price
        grand_total = total + shipping
        payment_id = 'ADMIN-TEST-{}'.format(timezone.now().strftime('%Y%m%d%H%M%S'))

        payment = Payment.objects.create(
            user=customer,
            payment_id=payment_id,
            payment_method='admin_test',
            amount_paid=str(grand_total),
            status='success',
            bank='bog',
            checkout_data={
                'language_code': 'ka',
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'email': customer.email,
                'phone': customer.phone_number,
                'address_line_1': 'თბილისი',
                'address_line_2': 'ტესტ მისამართი',
                'city': 'თბილისი',
                'state': '',
                'country': 'საქართველო',
            },
        )
        order = Order.objects.create(
            user=customer,
            payment=payment,
            order_number='',
            first_name=customer.first_name,
            last_name=customer.last_name,
            phone=customer.phone_number,
            email=customer.email,
            address_line_1='თბილისი',
            address_line_2='ტესტ მისამართი',
            city='თბილისი',
            country='საქართველო',
            order_total=grand_total,
            shipping_price=shipping,
            tax=Decimal('0.00'),
            status='New',
            ip=request.META.get('REMOTE_ADDR', ''),
            is_ordered=True,
        )
        order.order_number = '{}{}'.format(timezone.now().strftime('%Y%m%d'), order.id)
        order.save(update_fields=['order_number'])

        order_product = OrderProduct.objects.create(
            order=order,
            payment=payment,
            user=customer,
            product=product,
            color=str(variation.color) if variation and variation.color else '',
            size=str(variation.size) if variation and variation.size else '',
            quantity=1,
            variation=variation,
            product_price=unit_price,
            ordered=True,
        )

        try:
            _send_customer_order_email(
                request, order, [order_product], total, grand_total, shipping, TEST_CUSTOMER_EXTRA_EMAILS
            )
        except Exception as exc:
            order_url = request.build_absolute_uri('/ka/carts/payment_check/?id={}&show_order=1'.format(payment.p_number))
            self.message_user(
                request,
                'Test order was created, but the email failed: {}. Order page: {}'.format(exc, order_url),
                level='WARNING',
            )
            return HttpResponseRedirect(reverse('admin:accounts_testcustomer_changelist'))

        order_url = request.build_absolute_uri('/ka/carts/payment_check/?id={}&show_order=1'.format(payment.p_number))
        recipients = ', '.join([order.email] + TEST_CUSTOMER_EXTRA_EMAILS)
        self.message_user(request, 'Designed test email sent to {}. Order page: {}'.format(recipients, order_url))
        return HttpResponseRedirect(reverse('admin:accounts_testcustomer_changelist'))


class UserProfileAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        try:
            return format_html('<img src="{}" width="30" style="border-radius:50%;">'.format(object.profile_picture.url))
        except Exception:
            pass
    thumbnail.short_description = 'Profile Picture'
    list_display = ('thumbnail', 'user', 'city', 'state', 'country')


admin.site.register(Account, AccountAdmin)
admin.site.register(TestCustomer, TestCustomerAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
