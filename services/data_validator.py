"""
services/data_validator.py — Sistema de Validação Defensiva de Dados
Garante que NUNCA ocorram erros de conversão de tipo
"""
from typing import Any, Optional, Union, List, Dict
import re


class DataValidator:
    """Validador defensivo que sempre retorna valores seguros."""
    
    @staticmethod
    def to_float(value: Any, default: float = 0.0) -> float:
        """
        Converte qualquer valor para float de forma segura.
        NUNCA lança exceção.
        """
        if value is None:
            return default
            
        # Se já é número
        if isinstance(value, (int, float)):
            return float(value)
        
        # Se é string
        if isinstance(value, str):
            # Remove textos descritivos comuns
            if any(x in value.lower() for x in [
                'não encontrado', 'n/a', 'n/d', 'desconhecido', 
                'indisponível', 'necessita', 'sem informação',
                'não informado', 'não disponível'
            ]):
                return default
            
            # Remove caracteres não numéricos (mantém dígitos, ponto, vírgula, sinal)
            cleaned = re.sub(r'[^\d.,\-]', '', value)
            if not cleaned or cleaned in ['-', '.', ',']:
                return default
                
            # Substitui vírgula por ponto
            cleaned = cleaned.replace(',', '.')
            
            try:
                return float(cleaned)
            except (ValueError, TypeError):
                return default
        
        return default
    
    @staticmethod
    def to_int(value: Any, default: int = 0) -> int:
        """Converte para inteiro de forma segura."""
        try:
            float_val = DataValidator.to_float(value, default)
            return int(float_val)
        except:
            return default
    
    @staticmethod
    def to_string(value: Any, default: str = "") -> str:
        """Converte para string, removendo valores inválidos."""
        if value is None:
            return default
            
        if isinstance(value, str):
            # Remove strings que indicam ausência de dados
            if any(x in value.lower() for x in [
                'não encontrado', 'n/a', 'n/d', 'desconhecido',
                'indisponível', 'sem informação'
            ]):
                return default
            return value.strip()
        
        if isinstance(value, (list, dict)):
            return str(value) if value else default
            
        return str(value)
    
    @staticmethod
    def to_list(value: Any, default: Optional[List] = None) -> List:
        """Converte para lista, filtrando valores inválidos."""
        if default is None:
            default = []
            
        if value is None:
            return default
            
        if isinstance(value, list):
            # Filtra itens None ou vazios
            return [
                DataValidator.to_string(item) 
                for item in value 
                if item is not None and str(item).strip()
            ]
        
        if isinstance(value, str):
            if not value.strip() or value.lower() in ['n/a', 'n/d', 'nenhum']:
                return default
            return [value.strip()]
        
        return default
    
    @staticmethod
    def extract_number_from_text(text: str, default: float = 0.0) -> float:
        """
        Extrai o primeiro número encontrado em um texto.
        Exemplo: "Empresa possui 5000 hectares" -> 5000.0
        """
        if not text or not isinstance(text, str):
            return default
            
        # Procura por padrões numéricos
        patterns = [
            r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)',  # 1.000,50 ou 1,000.50
            r'(\d+[.,]?\d*)'  # 1000 ou 1000.5
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return DataValidator.to_float(matches[0], default)
        
        return default
    
    @staticmethod
    def validate_confidence(value: Any) -> float:
        """Valida e normaliza score de confiança (0-1)."""
        conf = DataValidator.to_float(value, 0.0)
        # Se veio em escala 0-100, normaliza
        if conf > 1.0:
            conf = conf / 100.0
        return max(0.0, min(1.0, conf))
    
    @staticmethod
    def clean_cnpj(value: Any) -> str:
        """Limpa e valida formato de CNPJ."""
        if not value:
            return ""
            
        cnpj = re.sub(r'[^\d]', '', str(value))
        
        # CNPJ deve ter 14 dígitos
        if len(cnpj) != 14:
            return ""
            
        # Valida se não é sequência repetida (00000000000000, etc)
        if len(set(cnpj)) == 1:
            return ""
            
        return cnpj
    
    @staticmethod
    def validate_dict_structure(data: Any, required_keys: List[str]) -> Dict:
        """
        Valida estrutura de dicionário, retornando dicionário seguro
        com todas as chaves requeridas.
        """
        if not isinstance(data, dict):
            return {key: None for key in required_keys}
        
        result = {}
        for key in required_keys:
            result[key] = data.get(key)
        
        return result


# Instância global para uso direto
validator = DataValidator()


# Funções de conveniência
def safe_float(value: Any, default: float = 0.0) -> float:
    """Wrapper rápido para conversão segura de float."""
    return validator.to_float(value, default)


def safe_int(value: Any, default: int = 0) -> int:
    """Wrapper rápido para conversão segura de int."""
    return validator.to_int(value, default)


def safe_str(value: Any, default: str = "") -> str:
    """Wrapper rápido para conversão segura de string."""
    return validator.to_string(value, default)


def safe_list(value: Any, default: Optional[List] = None) -> List:
    """Wrapper rápido para conversão segura de lista."""
    return validator.to_list(value, default)
