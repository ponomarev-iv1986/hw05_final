from django.test import Client, TestCase


class AboutURLTests(TestCase):
    """Тестирование URL приложения About."""

    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_urls_static(self):
        """Проверяем статичные страницы."""
        static_urls = [
            '/about/author/',
            '/about/tech/',
        ]
        for page in static_urls:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(
                    response.status_code,
                    200
                )

    def test_urls_static_template(self):
        """
        Проверяем вызываемые HTML-шаблоны
        статичных страниц.
        """
        template_urls_static = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for address, template in template_urls_static.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)
