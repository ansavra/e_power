import unittest
from app import app

class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def login_admin(self):
        self.client.get('/logout')
        return self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

    def test_unauthenticated_redirect(self):
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

    def test_login_page_renders(self):
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn('ចូលប្រើប្រាស់ប្រព័ន្ធ'.encode('utf-8'), res.data)
        self.assertIn(b'admin', res.data)

    def test_register_page_renders(self):
        res = self.client.get('/register')
        self.assertEqual(res.status_code, 200)
        self.assertIn('ចុះឈ្មោះគណនីថ្មី'.encode('utf-8'), res.data)

    def test_login_success(self):
        res = self.login_admin()
        self.assertEqual(res.status_code, 200)
        self.assertIn('ផ្ទាំងគ្រប់គ្រងទូទៅ'.encode('utf-8'), res.data)
        self.assertIn('Admin'.encode('utf-8'), res.data)

    def test_login_failure(self):
        res = self.client.post('/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('មិនត្រឹមត្រូវ'.encode('utf-8'), res.data)

    def test_register_and_login_new_user(self):
        import uuid
        test_username = f"user_{uuid.uuid4().hex[:6]}"
        res = self.client.post('/register', data={
            'full_name': 'សុខ តេស្ត (Sok Test)',
            'username': test_username,
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('ផ្ទាំងគ្រប់គ្រងទូទៅ'.encode('utf-8'), res.data)

    def test_dashboard(self):
        self.login_admin()
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'E-POWER', res.data)
        self.assertIn('អតិថិជនសរុប'.encode('utf-8'), res.data)

    def test_customers(self):
        self.login_admin()
        res = self.client.get('/customers')
        self.assertEqual(res.status_code, 200)
        self.assertIn('គ្រប់គ្រងព័ត៌មានអតិថិជន'.encode('utf-8'), res.data)

    def test_meter_reading_page(self):
        self.login_admin()
        res = self.client.get('/meter-reading')
        self.assertEqual(res.status_code, 200)
        self.assertIn('កត់ត្រាលេខកុងទ័រ'.encode('utf-8'), res.data)

    def test_billing_page(self):
        self.login_admin()
        res = self.client.get('/billing')
        self.assertEqual(res.status_code, 200)
        self.assertIn('វិក័យបត្រ'.encode('utf-8'), res.data)

    def test_logout(self):
        self.login_admin()
        res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn('ចូលប្រើប្រាស់ប្រព័ន្ធ'.encode('utf-8'), res.data)
        # Dashboard should now be protected again
        res_dash = self.client.get('/dashboard')
        self.assertEqual(res_dash.status_code, 302)

    def test_api_latest_reading(self):
        res = self.client.get('/api/customers/1/latest-reading')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('previous_reading', data)
        self.assertGreaterEqual(data['previous_reading'], 0)

    def test_api_calculate(self):
        # 45 kWh @ 400 KHR = 18,000 KHR
        res = self.client.post('/api/calculate', json={
            'previous_reading': 0,
            'current_reading': 45,
            'use_tiered': True
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['valid'])
        self.assertEqual(data['usage_kwh'], 45.0)
        self.assertEqual(data['total_amount'], 18000.0)

        # 70 kWh: 50*400 (20,000) + 20*600 (12,000) = 32,000 KHR
        res2 = self.client.post('/api/calculate', json={
            'previous_reading': 0,
            'current_reading': 70,
            'use_tiered': True
        })
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2['total_amount'], 32000.0)

    def test_api_calculate_custom_flat_rate(self):
        # 50 kWh @ 800 KHR flat rate = 40,000 KHR
        res = self.client.post('/api/calculate', json={
            'previous_reading': 0,
            'current_reading': 50,
            'use_tiered': False,
            'flat_rate': 800
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['valid'])
        self.assertEqual(data['usage_kwh'], 50.0)
        self.assertEqual(data['total_amount'], 40000.0)

    def test_print_invoice_a5(self):
        self.login_admin()
        res = self.client.get('/invoice/1/print')
        self.assertEqual(res.status_code, 200)
        data = res.data.decode('utf-8')
        self.assertIn('a5-page', data)
        self.assertIn('barcode-cust', data)
        self.assertIn('history-grid', data)
        self.assertIn('tear-off-badge', data)
        self.assertIn('VATIN', data)

    def test_admin_users_page_requires_admin(self):
        # 1. Unauthenticated gets redirected to /login
        res1 = self.client.get('/users')
        self.assertEqual(res1.status_code, 302)

        # 2. Staff user gets 403
        import uuid
        staff_user = f"staff_{uuid.uuid4().hex[:6]}"
        self.client.post('/register', data={
            'full_name': 'បុគ្គលិក តេស្ត',
            'username': staff_user,
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        res2 = self.client.get('/users')
        self.assertEqual(res2.status_code, 403)

        # 3. Admin gets 200
        self.login_admin()
        res3 = self.client.get('/users')
        self.assertEqual(res3.status_code, 200)
        self.assertIn('គ្រប់គ្រងអ្នកប្រើប្រាស់'.encode('utf-8'), res3.data)

    def test_admin_manage_users_crud(self):
        self.login_admin()
        import uuid
        uid_str = uuid.uuid4().hex[:6]
        new_user = f"ops_{uid_str}"

        # 1. Add user
        res_add = self.client.post('/api/users', json={
            'username': new_user,
            'password': 'password123',
            'full_name': 'អ្នកប្រតិបត្តិការ ថ្មី',
            'role': 'Staff'
        })
        self.assertEqual(res_add.status_code, 200)
        self.assertTrue(res_add.get_json()['success'])

        # Find user ID
        from services import UserService
        all_users = UserService.get_all()
        created_user = next((u for u in all_users if u['username'] == new_user), None)
        self.assertIsNotNone(created_user)
        target_id = created_user['user_id']

        # 2. Update role to Accountant
        res_role = self.client.post(f'/api/users/{target_id}/role', json={'role': 'Accountant'})
        self.assertEqual(res_role.status_code, 200)
        u_updated = UserService.get_by_id(target_id)
        self.assertEqual(u_updated['role'], 'Accountant')

        # 3. Reset password
        res_pw = self.client.post(f'/api/users/{target_id}/reset-password', json={'new_password': 'newsecretpass'})
        self.assertEqual(res_pw.status_code, 200)
        auth_user, _ = UserService.authenticate(new_user, 'newsecretpass')
        self.assertIsNotNone(auth_user)

        # 4. Attempt to delete self (admin ID 1) -> must fail
        res_del_self = self.client.post('/api/users/1/delete')
        self.assertEqual(res_del_self.status_code, 400)
        self.assertFalse(res_del_self.get_json()['success'])

        # 5. Delete newly created user -> must succeed
        res_del = self.client.post(f'/api/users/{target_id}/delete')
        self.assertEqual(res_del.status_code, 200)
        self.assertIsNone(UserService.get_by_id(target_id))

if __name__ == '__main__':
    unittest.main()
