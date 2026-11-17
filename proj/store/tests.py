from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import register, adregister, OTP, AdminOTP, SCNProduct, SCNOrder, SCNLatencyLog


class SCNPortalTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Admin
        self.admin = adregister.objects.create(
            username='Swastik Pandya',
            email='pandyaswastik2005@gmail.com',
            password='sompandya',
            confirm_password='sompandya',
            role='admin'
        )
        User.objects.create_superuser(
            username='Swastik Pandya',
            email='pandyaswastik2005@gmail.com',
            password='sompandya'
        )

        # Distributor 1 using demo email
        self.distributor = register.objects.create(
            username='Apex Pharma Distributor',
            email='pandyaswastik2005@gmail.com',
            password='distpassword',
            confirm_password='distpassword',
            role='distributor'
        )

        # Retailer 1 using SAME demo email
        self.retailer = register.objects.create(
            username='Apollo Retail Pharmacy',
            email='pandyaswastik2005@gmail.com',
            password='retailpassword',
            confirm_password='retailpassword',
            role='retailer'
        )

        # Medicine Product
        self.product = SCNProduct.objects.create(
            distributor=self.distributor,
            name='Paracetamol 500mg Tablets',
            category='Analgesics',
            sku='MED-TEST-001',
            price=6.50,
            stock_quantity=100,
            lead_time_hours=1.0
        )

    def test_unique_email_enforcement(self):
        # Register new distributor with fresh unique email -> should succeed
        resp1 = self.client.post(reverse('register_distributor'), {
            'Username': 'MedPlus Distributor',
            'email': 'medplus.unique@pharma.com',
            'password': 'password123',
            'confirm_pass': 'password123'
        })
        self.assertEqual(resp1.status_code, 302)
        self.assertTrue(register.objects.filter(username='MedPlus Distributor').exists())

        # Attempt to register another account with the DUPLICATE email -> should fail with error message
        resp2 = self.client.post(reverse('register_user'), {
            'Username': 'Care Chemist Store',
            'email': 'medplus.unique@pharma.com',
            'password': 'password123',
            'confirm_pass': 'password123'
        })
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, "already registered")

    def test_login_by_username_and_email(self):
        # Login with username
        resp1 = self.client.post(reverse('login_distributor'), {
            'email': 'Apex Pharma Distributor',
            'password': 'distpassword'
        })
        self.assertEqual(resp1.status_code, 302)
        self.assertEqual(self.client.session.get('user_name'), 'Apex Pharma Distributor')

    def test_order_placement_by_all(self):
        # Placed by guest / all
        order_resp = self.client.post(reverse('place_order'), {
            'product_id': self.product.id,
            'quantity': 10,
            'retailer_name': 'Apollo Retail Pharmacy',
            'retailer_email': 'pandyaswastik2005@gmail.com'
        })
        self.assertEqual(order_resp.status_code, 302)

        order = SCNOrder.objects.filter(product=self.product).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.quantity, 10)
        self.assertEqual(order.status, 'Processing')

        # Test receipt URL works
        rcp_resp = self.client.get(reverse('view_receipt', args=[order.order_id]))
        self.assertEqual(rcp_resp.status_code, 200)
        self.assertContains(rcp_resp, f'RCP-{order.order_id}')

    def test_order_dispatch_and_receive_permissions(self):
        order = SCNOrder.objects.create(
            order_id='ORD-SCN-TEST-100',
            retailer_name='Apollo Retail Pharmacy',
            retailer_email='pandyaswastik2005@gmail.com',
            distributor=self.distributor,
            product=self.product,
            quantity=5,
            total_price=32.50,
            status='Processing'
        )

        # 1. Retailer tries to dispatch (MUST FAIL)
        self.client.post(reverse('login_user'), {
            'email': 'Apollo Retail Pharmacy',
            'password': 'retailpassword'
        })
        disp_fail = self.client.post(reverse('update_order_status'), {
            'order_id': order.order_id,
            'new_status': 'Dispatched'
        })
        order.refresh_from_db()
        self.assertEqual(order.status, 'Processing')  # Blocked!

        # 2. Distributor dispatches (MUST SUCCEED)
        self.client.post(reverse('login_distributor'), {
            'email': 'Apex Pharma Distributor',
            'password': 'distpassword'
        })
        disp_ok = self.client.post(reverse('update_order_status'), {
            'order_id': order.order_id,
            'new_status': 'Dispatched'
        })
        order.refresh_from_db()
        self.assertEqual(order.status, 'Dispatched')

        # 3. Distributor tries to mark as Delivered/Received (MUST FAIL)
        rec_fail = self.client.post(reverse('update_order_status'), {
            'order_id': order.order_id,
            'new_status': 'Delivered'
        })
        order.refresh_from_db()
        self.assertEqual(order.status, 'Dispatched')  # Blocked!

        # 4. Retailer marks as Delivered/Received (MUST SUCCEED)
        self.client.post(reverse('login_user'), {
            'email': 'Apollo Retail Pharmacy',
            'password': 'retailpassword'
        })
        rec_ok = self.client.post(reverse('update_order_status'), {
            'order_id': order.order_id,
            'new_status': 'Delivered'
        })
        order.refresh_from_db()
        self.assertEqual(order.status, 'Delivered')
        self.assertIsNotNone(order.latency_recorded_hours)

    def test_stock_update_permissions(self):
        # Retailer tries to update stock (MUST FAIL)
        self.client.post(reverse('login_user'), {
            'email': 'Apollo Retail Pharmacy',
            'password': 'retailpassword'
        })
        fail_stock = self.client.post(reverse('update_product_stock'), {
            'product_id': self.product.id,
            'stock': 999,
            'lead_time': 0.5
        })
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 100)  # Unchanged!

        # Distributor updates stock (MUST SUCCEED)
        self.client.post(reverse('login_distributor'), {
            'email': 'Apex Pharma Distributor',
            'password': 'distpassword'
        })
        ok_stock = self.client.post(reverse('update_product_stock'), {
            'product_id': self.product.id,
            'stock': 750,
            'lead_time': 0.8
        })
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 750)
        self.assertEqual(float(self.product.lead_time_hours), 0.8)
