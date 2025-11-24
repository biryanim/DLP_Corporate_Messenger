import React, { useState } from 'react';
import './IncidentList.css';

// Статичные данные для примера
const STATIC_INCIDENTS = [
  {
    id: 1001,
    date: new Date('2025-11-23T12:34:56'),
    type: 'Персональные данные (ИНН)',
    user: 'john_doe',
    severity: 'high',
    action: 'БЛОКИРОВАНО'
  },
  {
    id: 1002,
    date: new Date('2025-11-23T11:15:30'),
    type: 'Номер банковской карты',
    user: 'alice.smith',
    severity: 'high',
    action: 'МАСКИРОВАНО'
  },
  {
    id: 1003,
    date: new Date('2025-11-23T10:45:12'),
    type: 'Контактная информация (Email)',
    user: 'bob_wilson',
    severity: 'medium',
    action: 'РАЗРЕШЕНО'
  },
  {
    id: 1004,
    date: new Date('2025-11-23T09:22:00'),
    type: 'Классификация (ДСП)',
    user: 'carol_jones',
    severity: 'high',
    action: 'КАРАНТИН'
  },
  {
    id: 1005,
    date: new Date('2025-11-23T08:10:45'),
    type: 'СНИЛС',
    user: 'david_brown',
    severity: 'high',
    action: 'БЛОКИРОВАНО'
  },
  {
    id: 1006,
    date: new Date('2025-11-22T16:55:20'),
    type: 'Номер телефона',
    user: 'emma_davis',
    severity: 'low',
    action: 'РАЗРЕШЕНО'
  },
  {
    id: 1007,
    date: new Date('2025-11-22T15:30:00'),
    type: 'Персональные данные (Паспорт)',
    user: 'frank_miller',
    severity: 'high',
    action: 'БЛОКИРОВАНО'
  },
  {
    id: 1008,
    date: new Date('2025-11-22T14:12:33'),
    type: 'Финансовые данные (Счёт)',
    user: 'grace_lee',
    severity: 'medium',
    action: 'МАСКИРОВАНО'
  }
];

function IncidentList() {
  const [incidents, setIncidents] = useState(STATIC_INCIDENTS);
  const [selectedIncidents, setSelectedIncidents] = useState(new Set());
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });

  // Форматирование даты
  const formatDate = (date) => {
    return new Intl.DateTimeFormat('ru-RU', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(date);
  };

  // Обработчик сортировки
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }

    const sortedIncidents = [...incidents].sort((a, b) => {
      let aValue = a[key];
      let bValue = b[key];

      if (key === 'date') {
        aValue = aValue.getTime();
        bValue = bValue.getTime();
      } else if (typeof aValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (direction === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setIncidents(sortedIncidents);
    setSortConfig({ key, direction });
  };

  // Обработчик выделения всех
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIncidents(new Set(incidents.map(i => i.id)));
    } else {
      setSelectedIncidents(new Set());
    }
  };

  // Обработчик выделения одного элемента
  const handleSelectIncident = (id) => {
    const newSelected = new Set(selectedIncidents);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIncidents(newSelected);
  };

  // Получение иконки сортировки
  const getSortIndicator = (key) => {
    if (sortConfig.key !== key) return '⇅';
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  return (
    <div className="incident-list-container">
      <div className="incident-list-header">
        <h2>Список инцидентов</h2>
        <p className="incident-count">Всего: {incidents.length}</p>
      </div>

      <div className="incident-list-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="🔍 Поиск по пользователю..."
            className="search-input"
          />
        </div>

        <div className="filter-badges">
          {selectedIncidents.size > 0 && (
            <span className="filter-badge">
              Выделено: {selectedIncidents.size}
            </span>
          )}
        </div>
      </div>

      <div className="table-wrapper">
        <table className="incidents-table">
          <thead>
            <tr>
              <th className="checkbox-column">
                <input
                  type="checkbox"
                  onChange={handleSelectAll}
                  checked={selectedIncidents.size === incidents.length && incidents.length > 0}
                  title="Выделить все"
                />
              </th>
              <th className="id-column">ID</th>
              <th className="sortable" onClick={() => handleSort('date')}>
                Дата {getSortIndicator('date')}
              </th>
              <th className="sortable" onClick={() => handleSort('type')}>
                Тип инцидента {getSortIndicator('type')}
              </th>
              <th className="sortable" onClick={() => handleSort('user')}>
                Пользователь {getSortIndicator('user')}
              </th>
              <th className="severity-column">Серьёзность</th>
              <th className="action-column">Действие</th>
            </tr>
          </thead>
          <tbody>
            {incidents.map((incident) => (
              <tr
                key={incident.id}
                className={`incident-row severity-${incident.severity} ${
                  selectedIncidents.has(incident.id) ? 'selected' : ''
                }`}
              >
                <td className="checkbox-column">
                  <input
                    type="checkbox"
                    checked={selectedIncidents.has(incident.id)}
                    onChange={() => handleSelectIncident(incident.id)}
                  />
                </td>
                <td className="id-column">#{incident.id}</td>
                <td className="date-column">
                  {formatDate(incident.date)}
                </td>
                <td className="type-column">
                  <span className="type-badge">{incident.type}</span>
                </td>
                <td className="user-column">
                  <span className="user-name">{incident.user}</span>
                </td>
                <td className="severity-column">
                  <span className={`badge badge-${incident.severity}`}>
                    {incident.severity === 'high' && '⚠️ Высокая'}
                    {incident.severity === 'medium' && '⚡ Средняя'}
                    {incident.severity === 'low' && 'ℹ️ Низкая'}
                  </span>
                </td>
                <td className="action-column">
                  <span className={`action-badge action-${incident.action.toLowerCase().replace(' ', '-')}`}>
                    {incident.action}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="incident-list-footer">
        <p className="footer-info">
          Показано {incidents.length} из {STATIC_INCIDENTS.length} инцидентов
        </p>
        <button className="btn-export">
          📥 Экспортировать
        </button>
      </div>
    </div>
  );
}

export default IncidentList;
