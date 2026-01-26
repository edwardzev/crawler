import unittest
from crawler.parser import HTMLParser

class TestParser(unittest.TestCase):
    def test_regex_extraction(self):
        html = """
        <html>
            <body>
                <div class="product-info">
                    <span>Product Code: 12345-ABC</span>
                </div>
                <div class="header">
                    <h1>My Product</h1>
                </div>
                <div class="price">
                    Price: $99.99
                </div>
            </body>
        </html>
        """
        parser = HTMLParser(html)
        
        selectors = {
            "title": ".header h1",
            "sku": ".product-info span :: regex:Product Code:\\s*([0-9A-Z-]+)",
            "price": ".price :: regex:([0-9.]+)"
        }
        
        data = parser.parse_product(selectors)
        
        self.assertEqual(data.get("title"), "My Product")
        self.assertEqual(data.get("sku"), "12345-ABC")
        self.assertEqual(data.get("price"), "99.99")

    def test_regex_attribute(self):
        html = """
        <html>
            <body>
                 <img id="main" src="/img/prod_555.jpg?v=123" />
            </body>
        </html>
        """
        parser = HTMLParser(html)
        
        selectors = {
            "image_id": "#main::src :: regex:prod_([0-9]+)"
        }
        
        data = parser.parse_product(selectors)
        self.assertEqual(data.get("image_id"), "555")

if __name__ == '__main__':
    unittest.main()
