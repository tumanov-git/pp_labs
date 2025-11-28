import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from roman_checker import (
    is_valid_roman,
    _extract_text_from_html,
    _iter_roman,
    _normalize_url,
    _read_url
)


class TestIsValidRoman:
    """Тесты для функции is_valid_roman()"""

    def test_valid_single_digits(self):
        """Тест валидных одиночных цифр"""
        assert is_valid_roman("I") is True
        assert is_valid_roman("V") is True
        assert is_valid_roman("X") is True
        assert is_valid_roman("L") is True
        assert is_valid_roman("C") is True
        assert is_valid_roman("D") is True
        assert is_valid_roman("M") is True

    def test_valid_compound_numbers(self):
        """Тест валидных составных чисел"""
        assert is_valid_roman("IV") is True
        assert is_valid_roman("IX") is True
        assert is_valid_roman("XL") is True
        assert is_valid_roman("XC") is True
        assert is_valid_roman("CD") is True
        assert is_valid_roman("CM") is True

    def test_valid_repeated_digits(self):
        """Тест валидных повторяющихся цифр"""
        assert is_valid_roman("II") is True
        assert is_valid_roman("III") is True
        assert is_valid_roman("XX") is True
        assert is_valid_roman("XXX") is True
        assert is_valid_roman("CC") is True
        assert is_valid_roman("CCC") is True
        assert is_valid_roman("MM") is True
        assert is_valid_roman("MMM") is True

    def test_valid_complex_numbers(self):
        """Тест валидных сложных чисел"""
        assert is_valid_roman("XIV") is True
        assert is_valid_roman("XIX") is True
        assert is_valid_roman("XLIV") is True
        assert is_valid_roman("XCIX") is True
        assert is_valid_roman("CDXLIV") is True
        assert is_valid_roman("CMXCIX") is True
        assert is_valid_roman("MMMCMXCIX") is True  # 3999

    def test_invalid_repeated_digits(self):
        """Тест невалидных повторяющихся цифр"""
        assert is_valid_roman("IIII") is False  # 4 I подряд
        assert is_valid_roman("VV") is False
        assert is_valid_roman("XXXX") is False
        assert is_valid_roman("LL") is False
        assert is_valid_roman("CCCC") is False
        assert is_valid_roman("DD") is False
        assert is_valid_roman("MMMM") is False  # больше 3999

    def test_invalid_combinations(self):
        """Тест невалидных комбинаций"""
        assert is_valid_roman("IVX") is False
        assert is_valid_roman("IXC") is False
        assert is_valid_roman("VX") is False
        assert is_valid_roman("LC") is False
        assert is_valid_roman("DM") is False

    def test_invalid_characters(self):
        """Тест невалидных символов"""
        assert is_valid_roman("ABC") is False
        assert is_valid_roman("123") is False
        assert is_valid_roman("I1") is False
        assert is_valid_roman("") is False

    def test_case_insensitive(self):
        """Тест регистронезависимости"""
        assert is_valid_roman("i") is True
        assert is_valid_roman("iv") is True
        assert is_valid_roman("XIV") is True
        assert is_valid_roman("xiv") is True

    def test_with_spaces(self):
        """Тест обработки пробелов"""
        assert is_valid_roman(" I ") is True
        assert is_valid_roman("  IV  ") is True


class TestExtractTextFromHtml:
    """Тесты для функции _extract_text_from_html()"""

    def test_simple_html(self):
        """Тест простого HTML"""
        html = "<p>Текст I и II</p>"
        result = _extract_text_from_html(html)
        assert "Текст I и II" in result

    def test_remove_script_tags(self):
        """Тест удаления script тегов"""
        html = "<script>alert('X')</script><p>Текст</p>"
        result = _extract_text_from_html(html)
        assert "alert" not in result
        assert "Текст" in result

    def test_remove_style_tags(self):
        """Тест удаления style тегов"""
        html = "<style>body { color: red; }</style><p>Текст</p>"
        result = _extract_text_from_html(html)
        assert "color" not in result
        assert "Текст" in result

    def test_remove_meta_and_link_tags(self):
        """Тест удаления meta и link тегов"""
        html = '<meta charset="utf-8"><link rel="stylesheet"><p>Текст</p>'
        result = _extract_text_from_html(html)
        assert "charset" not in result
        assert "stylesheet" not in result
        assert "Текст" in result

    def test_nested_tags(self):
        """Тест вложенных тегов"""
        html = "<div><span>I</span> и <span>II</span></div>"
        result = _extract_text_from_html(html)
        assert "I" in result
        assert "II" in result

    def test_empty_html(self):
        """Тест пустого HTML"""
        html = "<html></html>"
        result = _extract_text_from_html(html)
        assert result.strip() == ""

    def test_multiple_paragraphs(self):
        """Тест нескольких параграфов"""
        html = "<p>Первый параграф</p><p>Второй параграф</p>"
        result = _extract_text_from_html(html)
        assert "Первый параграф" in result
        assert "Второй параграф" in result

    def test_complex_html(self):
        """Тест сложного HTML с разными элементами"""
        html = """
        <html>
            <head><title>Заголовок</title></head>
            <body>
                <h1>Заголовок I</h1>
                <p>Текст с римскими числами II и III</p>
                <script>console.log('test');</script>
                <style>.class { color: red; }</style>
            </body>
        </html>
        """
        result = _extract_text_from_html(html)
        assert "Заголовок I" in result
        assert "II" in result
        assert "III" in result
        assert "console.log" not in result
        assert "color: red" not in result

    def test_remove_noscript_tags(self):
        """Тест удаления noscript тегов"""
        html = "<noscript>JavaScript required</noscript><p>Текст</p>"
        result = _extract_text_from_html(html)
        assert "JavaScript required" not in result
        assert "Текст" in result

    def test_html_with_no_removable_tags(self):
        """Тест HTML без удаляемых тегов"""
        html = "<p>Простой текст</p>"
        result = _extract_text_from_html(html)
        assert "Простой текст" in result


class TestIterRoman:
    """Тесты для функции _iter_roman()"""

    def test_single_roman_number(self):
        """Тест одного римского числа"""
        text = "В главе I"
        result = list(_iter_roman(text))
        assert result == ["I"]

    def test_multiple_roman_numbers(self):
        """Тест нескольких римских чисел"""
        text = "В главе I и II"
        result = list(_iter_roman(text))
        assert result == ["I", "II"]

    def test_no_roman_numbers(self):
        """Тест текста без римских чисел"""
        text = "Обычный текст без чисел"
        result = list(_iter_roman(text))
        assert result == []

    def test_mixed_text(self):
        """Тест смешанного текста"""
        text = "Главы I, II, III содержат важную информацию"
        result = list(_iter_roman(text))
        assert "I" in result
        assert "II" in result
        assert "III" in result

    def test_case_insensitive(self):
        """Тест регистронезависимости"""
        text = "i, ii, III"
        result = list(_iter_roman(text))
        assert "I" in result
        assert "II" in result
        assert "III" in result

    def test_complex_numbers(self):
        """Тест сложных римских чисел"""
        text = "Числа IV, IX, XL, XC, CD, CM"
        result = list(_iter_roman(text))
        assert "IV" in result
        assert "IX" in result
        assert "XL" in result
        assert "XC" in result
        assert "CD" in result
        assert "CM" in result

    def test_invalid_not_included(self):
        """Тест что невалидные числа не включаются"""
        text = "IIII VV XXXX"  # невалидные
        result = list(_iter_roman(text))
        assert result == []  # не должны быть найдены

    def test_large_numbers(self):
        """Тест больших чисел"""
        text = "MMMCMXCIX это 3999"
        result = list(_iter_roman(text))
        assert "MMMCMXCIX" in result

    def test_with_punctuation(self):
        """Тест с пунктуацией"""
        text = "Глава I. Раздел II, подраздел III."
        result = list(_iter_roman(text))
        assert "I" in result
        assert "II" in result
        assert "III" in result

    def test_empty_value_filtered(self):
        """Тест что пустые значения фильтруются"""
        # Создаём ситуацию, когда match.group() может быть пустым
        text = "   "  # только пробелы
        result = list(_iter_roman(text))
        assert result == []

    def test_invalid_roman_filtered(self):
        """Тест что невалидные римские числа фильтруются"""
        text = "IIII VV XXXX"  # невалидные, но могут быть найдены паттерном
        result = list(_iter_roman(text))
        assert result == []  # должны быть отфильтрованы is_valid_roman


class TestValidateUrl:
    """Тесты проверки валидности URL через _normalize_url()"""

    @staticmethod
    def _is_valid(url: str) -> bool:
        return bool(_normalize_url(url))

    def test_valid_http_url(self):
        """Тест валидного HTTP URL"""
        assert self._is_valid("http://example.com") is True

    def test_valid_https_url(self):
        """Тест валидного HTTPS URL"""
        assert self._is_valid("https://example.com") is True

    def test_valid_url_with_path(self):
        """Тест валидного URL с путём"""
        assert self._is_valid("https://example.com/path/to/page") is True

    def test_valid_url_with_query(self):
        """Тест валидного URL с параметрами"""
        assert self._is_valid("https://example.com/page?param=value") is True

    def test_valid_url_with_port(self):
        """Тест валидного URL с портом"""
        assert self._is_valid("http://example.com:8080") is True

    def test_no_scheme_auto_added(self):
        """Тест автоматического добавления схемы"""
        assert self._is_valid("example.com") is True

    def test_invalid_no_domain(self):
        """Тест URL без домена"""
        assert self._is_valid("https://") is False

    def test_invalid_empty_string(self):
        """Тест пустой строки"""
        assert self._is_valid("") is False

    def test_invalid_not_url(self):
        """Тест не-URL строки"""
        assert self._is_valid("not-a-url") is False
        assert self._is_valid("just text") is False

    def test_invalid_ftp_url(self):
        """FTP URL теперь невалиден"""
        assert self._is_valid("ftp://example.com") is False

    def test_urlparse_exception_handled(self):
        """Тест обработки некорректных строк"""
        assert self._is_valid("") is False  # Пустая строка
        assert self._is_valid("://") is False  # Некорректный формат


class TestNormalizeUrl:
    """Тесты для функции _normalize_url()"""

    def test_adds_https_when_missing(self):
        """Добавление схемы при отсутствии"""
        assert _normalize_url("example.com") == "https://example.com"

    def test_preserves_existing_scheme(self):
        """Схема не изменяется, если уже есть"""
        assert _normalize_url("http://example.com") == "http://example.com"

    def test_trims_whitespace(self):
        """Пробелы по краям удаляются"""
        assert _normalize_url("   ya.ru  ") == "https://ya.ru"

    def test_invalid_without_domain(self):
        """Отсутствие домена возвращает пустую строку"""
        assert _normalize_url("https://") == ""

    def test_empty_input(self):
        """Пустая строка"""
        assert _normalize_url("") == ""

    def test_invalid_format(self):
        """Некорректный формат"""
        assert _normalize_url("://broken") == ""


class TestReadUrl:
    """Тесты для функции _read_url()"""

    @patch('roman_checker.requests.get')
    def test_successful_request(self, mock_get):
        """Тест успешного запроса"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Текст I и II</body></html>"
        mock_response.apparent_encoding = "utf-8"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = _read_url("https://example.com")
        assert "Текст" in result
        assert "I" in result
        assert "II" in result
        mock_get.assert_called_once()

    @patch('roman_checker.requests.get')
    def test_invalid_url(self, mock_get):
        """Тест невалидного URL"""
        with pytest.raises(ValueError, match="Некорректный URL"):
            _read_url("not-a-url")
        mock_get.assert_not_called()

    @patch('roman_checker.requests.get')
    def test_http_error_401(self, mock_get):
        """Тест ошибки 401"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status = Mock(side_effect=requests.HTTPError())
        mock_get.return_value = mock_response

        with pytest.raises(requests.RequestException, match="Сайт требует авторизацию"):
            _read_url("https://example.com")

    @patch('roman_checker.requests.get')
    def test_http_error_403(self, mock_get):
        """Тест ошибки 403"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.raise_for_status = Mock(side_effect=requests.HTTPError())
        mock_get.return_value = mock_response

        with pytest.raises(requests.RequestException, match="Доступ к сайту запрещён"):
            _read_url("https://example.com")

    @patch('roman_checker.requests.get')
    def test_http_error_404(self, mock_get):
        """Тест ошибки 404"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status = Mock(side_effect=requests.HTTPError())
        mock_get.return_value = mock_response

        with pytest.raises(requests.RequestException, match="Страница не найдена"):
            _read_url("https://example.com")

    @patch('roman_checker.requests.get')
    def test_http_error_500(self, mock_get):
        """Тест ошибки 500"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status = Mock(side_effect=requests.HTTPError())
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            _read_url("https://example.com")

    @patch('roman_checker.requests.get')
    def test_connection_error(self, mock_get):
        """Тест ошибки соединения"""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        with pytest.raises(requests.ConnectionError):
            _read_url("https://example.com")

    @patch('roman_checker.requests.get')
    def test_timeout_error(self, mock_get):
        """Тест ошибки таймаута"""
        mock_get.side_effect = requests.Timeout("Request timeout")

        with pytest.raises(requests.Timeout):
            _read_url("https://example.com")

    @patch('roman_checker.requests.get')
    def test_html_extraction_integration(self, mock_get):
        """Тест интеграции с извлечением HTML"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <head><script>alert('test');</script></head>
            <body>
                <p>Римские числа: I, II, III</p>
                <style>body { color: red; }</style>
            </body>
        </html>
        """
        mock_response.apparent_encoding = "utf-8"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = _read_url("https://example.com")
        assert "I" in result
        assert "II" in result
        assert "III" in result
        assert "alert" not in result
        assert "color: red" not in result

    @patch('roman_checker.requests.get')
    def test_apparent_encoding_none(self, mock_get):
        """Тест когда apparent_encoding равен None (используется utf-8)"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Текст I</body></html>"
        mock_response.apparent_encoding = None
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = _read_url("https://example.com")
        assert "Текст" in result
        assert "I" in result

    @patch('roman_checker.requests.get')
    def test_http_error_other_codes(self, mock_get):
        """Тест других HTTP ошибок (не 401, 403, 404)"""
        mock_response = Mock()
        mock_response.status_code = 502  # Bad Gateway
        mock_response.raise_for_status = Mock(side_effect=requests.HTTPError())
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            _read_url("https://example.com")

    @patch('roman_checker.requests.get')
    def test_url_without_scheme_normalized(self, mock_get):
        """URL без схемы нормализуется перед запросом"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>I</body></html>"
        mock_response.apparent_encoding = "utf-8"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        _read_url("example.com")
        called_url = mock_get.call_args[0][0]
        assert called_url == "https://example.com"

