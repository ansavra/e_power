import unittest
from app import app

class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_dashboard(self):
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'E-POWER', res.data)
        self.assertIn('អតិថិជនសរុប'.encode('utf-8'), res.data)

    def test_customers(self):
        res = self.client.get('/customers')
        self.assertEqual(res.status_code, 200)
        self.assertIn('គ្រប់គ្រងព័ត៌មានអតិថិជន'.encode('utf-8'), res.data)

    def test_meter_reading_page(self):
        res = self.client.get('/meter-reading')
        self.assertEqual(res.status_code, 200)
        self.assertIn('កត់ត្រាលេខកុងទ័រ'.encode('utf-8'), res.data)

    def test_billing_page(self):
        res = self.client.get('/billing')
        self.assertEqual(res.status_code, 200)
        self.assertIn('វិក័យបត្រ'.encode('utf-8'), res.data)

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
        res = self.client.get('/invoice/1/print')
        self.assertEqual(res.status_code, 200)
        data = res.data.decode('utf-8')
        self.assertIn('a5-page', data)
        self.assertIn('barcode-cust', data)
        self.assertIn('history-grid', data)
        self.assertIn('tear-off-badge', data)
        self.assertIn('VATIN', data)

if __name__ == '__main__':
    unittest.main()
