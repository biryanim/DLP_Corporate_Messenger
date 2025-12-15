import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './IncidentList.css';

export default function IncidentList() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedIncidents, setSelectedIncidents] = useState(new Set());
  const [sortConfig, setSortConfig] = useState({ key: 'timestamp', direction: 'desc' });

  // Функция загрузки данных с бэкенда
  const fetchIncidents = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/incidents', {
        params: {
          limit: 100,
          offset: 0
        }
      });
      
      // Добавляем логирование для отладки
      console.log('Получены данные с бэкенда:', response.data);
      
      // Проверяем разные возможные структуры данных
      let incidentsData = [];
      
      if (Array.isArray(response.data)) {
        // Если ответ - массив
        incidentsData = response.data;
      } else if (response.data.incidents && Array.isArray(response.data.incidents)) {
        // Если ответ { incidents: [...] }
        incidentsData = response.data.incidents;
      } else if (response.data.data && Array.isArray(response.data.data)) {
        // Если ответ { data: [...] }
        incidentsData = response.data.data;
      } else if (response.data.results && Array.isArray(response.data.results)) {
        // Если ответ { results: [...] }
        incidentsData = response.data.results;
      } else {
        // Если структура неизвестна, пытаемся преобразовать объект в массив
        incidentsData = Object.values(response.data);
        if (!Array.isArray(incidentsData)) {
          incidentsData = [];
        }
      }
      
      console.log('Обработанные инциденты:', incidentsData);
      
      // Преобразуем данные, если нужно
      const formattedIncidents = incidentsData.map(incident => ({
        id: incident.id || incident._id || Math.random().toString(36).substr(2, 9),
        timestamp: incident.timestamp || incident.date || incident.created_at || new Date().toISOString(),
        incident_type: incident.incident_type || incident.type || incident.category || 'Unknown',
        user_id: incident.user_id || incident.user || incident.employee_id || 'N/A',
        platform: incident.platform || incident.source || incident.channel || 'Unknown',
        action: incident.action || incident.response || 'NOTIFY',
        // Добавляем другие поля, которые могут быть нужны
        ...incident
      }));
      
      setIncidents(formattedIncidents);
      setError(null);
    } catch (err) {
      console.error('Ошибка загрузки инцидентов:', err);
      setError(err.response?.data?.message || err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  // Первоначальная загрузка данных
  useEffect(() => {
    fetchIncidents();
  }, []);

  // Поллинг каждые 3 секунды
  useEffect(() => {
    const interval = setInterval(() => {
      fetchIncidents();
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // Сортировка
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Применение сортировки
  const sortedIncidents = React.useMemo(() => {
    let sortableIncidents = [...incidents];
    if (sortConfig.key && sortableIncidents.length > 0) {
      sortableIncidents.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        // Если значения undefined или null
        if (aValue == null) aValue = '';
        if (bValue == null) bValue = '';

        // Для даты
        if (sortConfig.key === 'timestamp') {
          const dateA = new Date(aValue);
          const dateB = new Date(bValue);
          if (sortConfig.direction === 'asc') {
            return dateA - dateB;
          } else {
            return dateB - dateA;
          }
        }

        // Для строк
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          if (sortConfig.direction === 'asc') {
            return aValue.localeCompare(bValue);
          } else {
            return bValue.localeCompare(aValue);
          }
        }

        // Для чисел
        if (sortConfig.direction === 'asc') {
          return aValue < bValue ? -1 : (aValue > bValue ? 1 : 0);
        } else {
          return aValue > bValue ? -1 : (aValue < bValue ? 1 : 0);
        }
      });
    }
    return sortableIncidents;
  }, [incidents, sortConfig]);

  // Выбор инцидентов
  const toggleIncidentSelection = (id) => {
    const newSelected = new Set(selectedIncidents);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIncidents(newSelected);
  };

  const toggleSelectAll = () => {
    if (selectedIncidents.size === incidents.length && incidents.length > 0) {
      setSelectedIncidents(new Set());
    } else {
      setSelectedIncidents(new Set(incidents.map(inc => inc.id)));
    }
  };

  // Открыть Kibana для расследования
  const handleInvestigate = (incidentId) => {
    const kibanaUrl = `http://localhost:5601/app/discover#/?_a=(query:(language:kuery,query:'incident_id:${incidentId}'))`;
    window.open(kibanaUrl, '_blank');
  };

  // Форматирование даты
  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Некорректная дата';
      }
      return date.toLocaleString('ru-RU', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (error) {
      return dateString || 'Дата не указана';
    }
  };

  // Определение серьезности по типу
  const getSeverityClass = (incidentType) => {
    if (!incidentType) return 'low';
    
    const typeStr = incidentType.toString().toLowerCase();
    if (typeStr.includes('инн') || typeStr.includes('снилс') || typeStr.includes('банковская') || typeStr.includes('карта') || typeStr.includes('credit') || typeStr.includes('card')) {
      return 'high';
    }
    if (typeStr.includes('email') || typeStr.includes('почта') || typeStr.includes('телефон') || typeStr.includes('phone')) {
      return 'medium';
    }
    return 'low';
  };

  // Получение бейджа действия
  const getActionBadge = (action) => {
    if (!action) return { text: 'НЕТ ДЕЙСТВИЯ', class: 'default' };
    
    const actionStr = action.toString().toUpperCase();
    const badges = {
      'BLOCK': { text: 'БЛОКИРОВАНО', class: 'blocked' },
      'MASK': { text: 'МАСКИРОВАНО', class: 'masked' },
      'ALLOW': { text: 'РАЗРЕШЕНО', class: 'allowed' },
      'QUARANTINE': { text: 'КАРАНТИН', class: 'quarantine' },
      'NOTIFY': { text: 'УВЕДОМЛЕНИЕ', class: 'notify' }
    };
    
    return badges[actionStr] || { text: action, class: 'default' };
  };

  if (loading && incidents.length === 0) {
    return (
      <div className="incident-list-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Загрузка инцидентов...</p>
        </div>
      </div>
    );
  }

  if (error && incidents.length === 0) {
    return (
      <div className="incident-list-container">
        <div className="error-message">
          <h3>⚠️ Ошибка загрузки данных</h3>
          <p>{error}</p>
          <button onClick={fetchIncidents} className="retry-button">
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="incident-list-container">
      <div className="incident-header">
        <h2>📋 Список инцидентов безопасности</h2>
        <div className="header-actions">
          <span className="incident-count">
            Всего: {incidents.length} | Выбрано: {selectedIncidents.size}
          </span>
          <button 
            onClick={fetchIncidents} 
            className="refresh-button"
            disabled={loading}
          >
            🔄 Обновить
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          ⚠️ Ошибка обновления данных: {error}
        </div>
      )}

      <div className="table-wrapper">
        <table className="incident-table">
          <thead>
            <tr>
              <th className="checkbox-column">
                <input
                  type="checkbox"
                  checked={incidents.length > 0 && selectedIncidents.size === incidents.length}
                  onChange={toggleSelectAll}
                  disabled={incidents.length === 0}
                />
              </th>
              <th onClick={() => handleSort('timestamp')} className="sortable">
                Дата
                {sortConfig.key === 'timestamp' && (
                  <span className="sort-indicator">
                    {sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('incident_type')} className="sortable">
                Тип инцидента
                {sortConfig.key === 'incident_type' && (
                  <span className="sort-indicator">
                    {sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort('user_id')} className="sortable">
                Пользователь
                {sortConfig.key === 'user_id' && (
                  <span className="sort-indicator">
                    {sortConfig.direction === 'asc' ? ' ↑' : ' ↓'}
                  </span>
                )}
              </th>
              <th>Платформа</th>
              <th>Действие</th>
              <th>Операции</th>
            </tr>
          </thead>
          <tbody>
            {sortedIncidents.length === 0 ? (
              <tr>
                <td colSpan="7" className="empty-state">
                  {loading ? 'Загрузка...' : 'Инциденты не найдены'}
                </td>
              </tr>
            ) : (
              sortedIncidents.map((incident) => (
                <tr
                  key={incident.id}
                  className={`incident-row severity-${getSeverityClass(incident.incident_type)}`}
                >
                  <td className="checkbox-column">
                    <input
                      type="checkbox"
                      checked={selectedIncidents.has(incident.id)}
                      onChange={() => toggleIncidentSelection(incident.id)}
                    />
                  </td>
                  <td className="date-column">
                    {formatDate(incident.timestamp)}
                  </td>
                  <td className="type-column">
                    <span className={`severity-badge ${getSeverityClass(incident.incident_type)}`}>
                      {incident.incident_type || 'Не указан'}
                    </span>
                  </td>
                  <td className="user-column">
                    <code>{incident.user_id || 'N/A'}</code>
                  </td>
                  <td className="platform-column">
                    {incident.platform || 'N/A'}
                  </td>
                  <td className="action-column">
                    <span className={`action-badge ${getActionBadge(incident.action).class}`}>
                      {getActionBadge(incident.action).text}
                    </span>
                  </td>
                  <td className="operations-column">
                    <button
                      onClick={() => handleInvestigate(incident.id)}
                      className="investigate-button"
                      title="Открыть в Kibana для расследования"
                    >
                      🔍 Investigate
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {loading && incidents.length > 0 && (
        <div className="updating-indicator">
          ⟳ Обновление данных...
        </div>
      )}
    </div>
  );
}