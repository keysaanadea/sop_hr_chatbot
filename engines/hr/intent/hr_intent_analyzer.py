"""
HR Intent Analyzer
Mendeteksi dua intent berbeda:
1. Apakah ini query DATA HR? (untuk routing tools.py)
2. Apakah user MAU grafik sekarang? (untuk visualization flow)
"""

import re
from typing import Dict


class HRIntentAnalyzer:
    """
    Menganalisis dua niat yang berbeda:
    1. is_hr_data_query: Apakah ini query tentang data HR/karyawan?
    2. wants_visualization: Apakah user eksplisit minta grafik/chart?
    """
    
    def __init__(self):
        # Keywords yang mengindikasikan query tentang DATA HR/karyawan
        self.hr_data_keywords = [
            'karyawan', 'employee', 'pegawai', 'staff',
            'gaji', 'salary', 'payroll', 
            'department', 'departemen', 'divisi',
            'jumlah karyawan', 'employee count',
            'data karyawan', 'employee data',
            'statistik hr', 'hr statistics',
            'performa karyawan', 'employee performance',
            'database karyawan', 'employee database',
            'rekrutmen', 'recruitment', 'hiring',
            'turnover', 'resign', 'attrition',
            'absensi', 'attendance', 'kehadiran'
        ]
        
        # Keywords yang mengindikasikan user MAU visualisasi
        self.viz_keywords = [
            'grafik', 'chart', 'graph', 'plot', 'visualisasi', 'visual',
            'diagram', 'bar', 'pie', 'line', 'scatter', 'histogram',
            'tampilkan dalam', 'buatkan grafik', 'lihat dalam bentuk',
            'dashboard', 'summary visual', 'buatkan chart'
        ]
        
        # Keywords yang mengindikasikan user hanya mau data
        self.data_only_keywords = [
            'data saja', 'tanpa grafik', 'raw data', 'tabel saja',
            'list', 'daftar', 'export data', 'unduh data'
        ]
    
    def analyze(self, question: str) -> Dict[str, bool]:
        """
        Analisis dua intent berbeda untuk HR query
        
        Args:
            question: Pertanyaan user dalam bahasa natural
            
        Returns:
            Dict dengan keys:
            - 'is_hr_data_query': Apakah ini tentang data HR?
            - 'wants_visualization': Apakah user mau grafik?
        """
        question_lower = question.lower()
        
        # 1. Deteksi apakah ini HR data query
        is_hr_query = self._is_hr_data_query(question_lower)
        
        # 2. Deteksi apakah user wants visualization
        wants_viz = self._wants_visualization(question_lower)
        
        return {
            "is_hr_data_query": is_hr_query,
            "wants_visualization": wants_viz
        }
    
    def _is_hr_data_query(self, question_lower: str) -> bool:
        """
        Deteksi apakah ini query tentang data HR/karyawan
        Untuk routing di tools.py
        """
        # Check explicit HR data keywords
        for keyword in self.hr_data_keywords:
            if keyword in question_lower:
                return True
        
        # Check for patterns yang biasanya HR-related
        hr_patterns = [
            r'berapa\s+.*?(karyawan|employee|pegawai)',
            r'jumlah\s+.*?(karyawan|employee|staff)',
            r'distribusi\s+.*?(gaji|salary|department)',
            r'rata-rata\s+.*?(gaji|performa|score)',
            r'total\s+.*?(karyawan|employee|pegawai)'
        ]
        
        for pattern in hr_patterns:
            if re.search(pattern, question_lower):
                return True
        
        return False
    
    def _wants_visualization(self, question_lower: str) -> bool:
        """
        Deteksi apakah user eksplisit minta visualisasi
        Untuk visualization flow di hr_service.py
        """
        # Check explicit data-only request
        for keyword in self.data_only_keywords:
            if keyword in question_lower:
                return False
        
        # Check visualization keywords
        viz_score = 0
        for keyword in self.viz_keywords:
            if keyword in question_lower:
                viz_score += 1
        
        # Simple rule: jika ada viz keywords, assume mau visualisasi
        wants_viz = viz_score > 0
        
        # Additional heuristics untuk visualization
        if not wants_viz:
            # Check for question patterns yang usually need visualization
            viz_patterns = [
                r'tren\s+\w+',  # "tren penjualan", "tren karyawan"
                r'perbandingan\s+\w+',  # "perbandingan department"
                r'distribusi\s+\w+',  # "distribusi gaji"
                r'bagaimana\s+\w+.*naik|turun',  # "bagaimana performa naik"
            ]
            
            for pattern in viz_patterns:
                if re.search(pattern, question_lower):
                    wants_viz = True
                    break
        
        return wants_viz
    
    
    def get_confidence_reason(self, question: str) -> Dict[str, str]:
        """
        Memberikan alasan untuk kedua keputusan intent
        Untuk debugging dan transparency
        """
        result = self.analyze(question)
        question_lower = question.lower()
        
        reasons = {}
        
        # Reason for HR data query detection
        if result["is_hr_data_query"]:
            for keyword in self.hr_data_keywords:
                if keyword in question_lower:
                    reasons["hr_query_reason"] = f"HR data keyword detected: '{keyword}'"
                    break
            else:
                reasons["hr_query_reason"] = "HR data pattern detected"
        else:
            reasons["hr_query_reason"] = "No HR data indicators found"
        
        # Reason for visualization intent detection
        if not result["wants_visualization"]:
            for keyword in self.data_only_keywords:
                if keyword in question_lower:
                    reasons["viz_reason"] = f"Data-only explicitly requested: '{keyword}'"
                    break
            else:
                reasons["viz_reason"] = "No visualization indicators detected"
        else:
            for keyword in self.viz_keywords:
                if keyword in question_lower:
                    reasons["viz_reason"] = f"Visualization keyword detected: '{keyword}'"
                    break
            else:
                reasons["viz_reason"] = "Question pattern suggests visualization"
        
        return reasons