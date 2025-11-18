"""
Sistema de Plugins do SimpleNFE

Plugins devem herdar de BasePlugin e implementar os métodos necessários.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BasePlugin(ABC):
    """Classe base para todos os plugins do SimpleNFE"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nome do plugin"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Versão do plugin"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição do plugin"""
        pass
    
    @property
    @abstractmethod
    def author(self) -> str:
        """Autor do plugin"""
        pass
    
    @abstractmethod
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """
        Inicializa o plugin com contexto da aplicação
        
        Args:
            app_context: Dicionário com referências da aplicação
                - 'app': Instância principal do app
                - 'extracted_items': Lista de itens extraídos
                - 'config': Configurações do sistema
        
        Returns:
            True se inicialização foi bem sucedida
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Executa a funcionalidade principal do plugin
        
        Args:
            **kwargs: Argumentos específicos do plugin
        
        Returns:
            Resultado da execução (pode ser qualquer tipo)
        """
        pass
    
    def get_menu_label(self) -> str:
        """Label para aparecer no menu (opcional)"""
        return self.name
    
    def get_toolbar_icon(self) -> Optional[str]:
        """Ícone emoji para toolbar (opcional)"""
        return None
    
    def cleanup(self) -> None:
        """Limpeza ao desabilitar plugin (opcional)"""
        pass
    
    def get_settings_ui(self) -> Optional[Dict[str, Any]]:
        """
        Define interface de configurações do plugin (opcional)
        
        Returns:
            Dicionário com definição de campos de configuração
            Exemplo: {
                'campos': [
                    {'nome': 'api_key', 'tipo': 'text', 'label': 'API Key'},
                    {'nome': 'ativo', 'tipo': 'checkbox', 'label': 'Ativar'},
                ]
            }
        """
        return None
