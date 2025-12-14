from elasticsearch import Elasticsearch
from typing import List, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """
    Сервис для работы с Elasticsearch.
    Индексирование, поиск и управление инцидентами.
    """
    
    def __init__(self, hosts: List[str] = None):
        """
        Инициализация сервиса Elasticsearch.
        
        Args:
            hosts: Список хостов Elasticsearch (например, ['localhost:9200'])
        """
        if hosts is None:
            hosts = ['localhost:9200']
        
        try:
            self.client = Elasticsearch(hosts=hosts)
            
            if self.client.ping():
                logger.info(f"✅ Подключение к Elasticsearch успешно: {hosts}")
            else:
                logger.warning(f"⚠️ Не удалось подключиться к Elasticsearch: {hosts}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка при подключении к Elasticsearch: {str(e)}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Проверить, подключен ли к Elasticsearch"""
        try:
            return self.client is not None and self.client.ping()
        except:
            return False
    
    def create_index(self, index: str, mappings: Dict = None):
        """
        Создать индекс с отображением полей.
        
        Args:
            index: Название индекса
            mappings: Отображение полей
        """
        try:
            if self.client.indices.exists(index=index):
                logger.info(f"ℹ️ Индекс уже существует: {index}")
                return
            
            if mappings is None:
                mappings = self._default_incident_mappings()
            
            self.client.indices.create(index=index, body=mappings)
            logger.info(f"✅ Индекс создан: {index}")
        
        except Exception as e:
            logger.error(f"❌ Ошибка при создании индекса: {str(e)}")
            raise
    
    def _default_incident_mappings(self) -> Dict:
        """Получить стандартное отображение для инцидентов"""
        return {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "scan_id": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "user_id": {"type": "keyword"},
                    "channel_id": {"type": "keyword"},
                    "incident_type": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "pattern_matched": {"type": "text"},
                    "original_text": {"type": "text", "index": False},
                    "context": {"type": "text"},
                    "action": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "is_encrypted": {"type": "boolean"}
                }
            }
        }
    
    def index_document(
        self,
        index: str,
        document: Dict,
        doc_id: Optional[str] = None
    ) -> Dict:
        """
        Индексировать документ в Elasticsearch.
        
        Args:
            index: Название индекса
            document: Документ для индексирования
            doc_id: ID документа (опционально)
        
        Returns:
            Dict: Результат индексирования
        """
        try:
            self.create_index(index)
            
            result = self.client.index(
                index=index,
                document=document,
                id=doc_id
            )
            
            logger.info(f"✅ Документ индексирован: {index}/{result['_id']}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Ошибка при индексировании: {str(e)}")
            raise
    
    def search_incidents(
        self,
        index: str,
        filters: Dict = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "timestamp",
        order: str = "desc"
    ) -> List[Dict]:
        """
        Поиск инцидентов в Elasticsearch.
        
        Args:
            index: Название индекса
            filters: Фильтры поиска
            limit: Максимальное количество результатов
            offset: Смещение
            sort_by: Поле для сортировки
            order: Порядок сортировки (asc, desc)
        
        Returns:
            List[Dict]: Список инцидентов
        """
        try:
            query_body = {"bool": {"must": []}}
            
            if filters:
                for key, value in filters.items():
                    query_body["bool"]["must"].append({"term": {key: value}})
            
            body = {
                "query": query_body if query_body["bool"]["must"] else {"match_all": {}},
                "size": limit,
                "from": offset,
                "sort": [{sort_by: {"order": order}}]
            }
            
            response = self.client.search(index=index, body=body)
            
            incidents = []
            for hit in response['hits']['hits']:
                doc = hit['_source']
                doc['_id'] = hit['_id']
                incidents.append(doc)
            
            logger.info(f"✅ Найдено инцидентов: {len(incidents)}")
            return incidents
        
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске: {str(e)}")
            raise
    
    def get_incident_by_id(self, index: str, doc_id: str) -> Optional[Dict]:
        """
        Получить инцидент по ID.
        
        Args:
            index: Название индекса
            doc_id: ID документа
        
        Returns:
            Optional[Dict]: Документ или None
        """
        try:
            result = self.client.get(index=index, id=doc_id)
            return result['_source']
        
        except Exception as e:
            logger.error(f"❌ Ошибка при получении документа: {str(e)}")
            return None
    
    def update_incident(
        self,
        index: str,
        doc_id: str,
        updates: Dict
    ) -> Dict:
        """
        Обновить инцидент.
        
        Args:
            index: Название индекса
            doc_id: ID документа
            updates: Обновления
        
        Returns:
            Dict: Результат обновления
        """
        try:
            result = self.client.update(
                index=index,
                id=doc_id,
                body={"doc": updates}
            )
            logger.info(f"✅ Инцидент обновлён: {index}/{doc_id}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении: {str(e)}")
            raise
    
    def delete_incident(self, index: str, doc_id: str) -> Dict:
        """
        Удалить инцидент.
        
        Args:
            index: Название индекса
            doc_id: ID документа
        
        Returns:
            Dict: Результат удаления
        """
        try:
            result = self.client.delete(index=index, id=doc_id)
            logger.info(f"✅ Инцидент удалён: {index}/{doc_id}")
            return result
        
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении: {str(e)}")
            raise
    
    def get_statistics(self, index: str) -> Dict:
        """
        Получить статистику по индексу.
        
        Args:
            index: Название индекса
        
        Returns:
            Dict: Статистика
        """
        try:
            stats = self.client.indices.stats(index=index)
            count = self.client.count(index=index)
            
            return {
                "index": index,
                "document_count": count['count'],
                "size_in_bytes": stats['indices'][index]['primaries']['store']['size_in_bytes'],
                "number_of_shards": stats['indices'][index]['primaries']['indexing']['index_total']
            }
        
        except Exception as e:
            logger.error(f"❌ Ошибка при получении статистики: {str(e)}")
            return {}
    
    def close(self):
        """Закрыть подключение к Elasticsearch"""
        try:
            if self.client:
                self.client.close()
                logger.info("✅ Подключение к Elasticsearch закрыто")
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии подключения: {str(e)}")
