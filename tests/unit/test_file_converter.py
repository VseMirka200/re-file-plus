"""Тесты для конвертации файлов."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.file_converter import FileConverter


class TestFileConverter:
    """Тесты для класса FileConverter."""
    
    def test_initialization(self):
        """Тест: инициализация FileConverter."""
        converter = FileConverter()
        
        assert converter is not None
        assert hasattr(converter, 'convert_file')
    
    def test_get_pdf_library_pypdf2(self):
        """Тест: получение библиотеки PyPDF2."""
        converter = FileConverter()
        
        with patch('core.file_converter.PyPDF2') as mock_pypdf2:
            mock_pypdf2.PdfReader = Mock
            mock_pypdf2.PdfWriter = Mock
            
            PdfReader, PdfWriter, available = converter._get_pdf_library()
            
            assert available is True
            assert PdfReader is not None
            assert PdfWriter is not None
    
    def test_get_pdf_library_pypdf(self):
        """Тест: получение библиотеки pypdf (fallback)."""
        converter = FileConverter()
        
        with patch('core.file_converter.PyPDF2', side_effect=ImportError):
            with patch('core.file_converter.pypdf') as mock_pypdf:
                mock_pypdf.PdfReader = Mock
                mock_pypdf.PdfWriter = Mock
                
                PdfReader, PdfWriter, available = converter._get_pdf_library()
                
                assert available is True
                assert PdfReader is not None
                assert PdfWriter is not None
    
    def test_get_pdf_library_not_available(self):
        """Тест: библиотека PDF недоступна."""
        converter = FileConverter()
        
        with patch('core.file_converter.PyPDF2', side_effect=ImportError):
            with patch('core.file_converter.pypdf', side_effect=ImportError):
                PdfReader, PdfWriter, available = converter._get_pdf_library()
                
                assert available is False
                assert PdfReader is None
                assert PdfWriter is None
    
    def test_find_pdf_in_source_directory(self, tmp_path):
        """Тест: поиск PDF в директории исходного файла."""
        converter = FileConverter()
        file_path = tmp_path / "document.docx"
        file_path.write_text("test")
        
        pdf_path = converter._find_pdf_in_source_directory(str(file_path))
        
        expected_pdf = os.path.join(
            str(tmp_path),
            "document.pdf"
        )
        assert pdf_path == expected_pdf
    

