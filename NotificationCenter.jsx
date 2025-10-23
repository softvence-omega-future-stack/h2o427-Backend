import React, { useState, useEffect } from 'react';
import { Bell, Check, X, Trash2, Eye, EyeOff } from 'lucide-react';

/**
 * Notification Component for H2O427 Backend
 * 
 * Features:
 * - Display notification list
 * - Unread count badge
 * - Mark as read/unread
 * - Delete notifications
 * - Real-time updates (polling)
 * - Filter by read status
 */

const NotificationCenter = ({ apiBaseUrl = 'http://localhost:8000/api', token }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState('all'); // 'all', 'unread', 'read'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (filter === 'unread') {
        params.append('is_read', 'false');
      } else if (filter === 'read') {
        params.append('is_read', 'true');
      }

      const response = await fetch(`${apiBaseUrl}/notifications/?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error('Failed to fetch notifications');

      const data = await response.json();
      setNotifications(data.results || []);
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch unread count
  const fetchUnreadCount = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/notifications/unread-count/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to fetch unread count');

      const data = await response.json();
      setUnreadCount(data.unread_count);
    } catch (err) {
      console.error('Error fetching unread count:', err);
    }
  };

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      const response = await fetch(`${apiBaseUrl}/notifications/mark-read/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          notification_ids: [notificationId],
          is_read: true,
        }),
      });

      if (!response.ok) throw new Error('Failed to mark as read');

      // Update local state
      setNotifications(prev =>
        prev.map(notif =>
          notif.id === notificationId ? { ...notif, is_read: true } : notif
        )
      );
      fetchUnreadCount();
    } catch (err) {
      console.error('Error marking as read:', err);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/notifications/mark-all-read/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to mark all as read');

      await fetchNotifications();
      await fetchUnreadCount();
    } catch (err) {
      console.error('Error marking all as read:', err);
    }
  };

  // Delete notification
  const deleteNotification = async (notificationId) => {
    try {
      const response = await fetch(`${apiBaseUrl}/notifications/${notificationId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to delete notification');

      setNotifications(prev => prev.filter(notif => notif.id !== notificationId));
      fetchUnreadCount();
    } catch (err) {
      console.error('Error deleting notification:', err);
    }
  };

  // Clear all read notifications
  const clearReadNotifications = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/notifications/clear-read/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to clear read notifications');

      await fetchNotifications();
    } catch (err) {
      console.error('Error clearing read notifications:', err);
    }
  };

  // Initial fetch and polling
  useEffect(() => {
    if (token) {
      fetchNotifications();
      fetchUnreadCount();

      // Poll for new notifications every 30 seconds
      const interval = setInterval(() => {
        fetchUnreadCount();
        if (isOpen) {
          fetchNotifications();
        }
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [token, filter, isOpen]);

  // Get notification icon and color based on category
  const getCategoryStyle = (category) => {
    const styles = {
      background_check: { bg: 'bg-blue-100', text: 'text-blue-800', icon: '🔍' },
      subscription: { bg: 'bg-green-100', text: 'text-green-800', icon: '💳' },
      payment: { bg: 'bg-red-100', text: 'text-red-800', icon: '💰' },
      report: { bg: 'bg-orange-100', text: 'text-orange-800', icon: '📄' },
      general: { bg: 'bg-gray-100', text: 'text-gray-800', icon: '📢' },
    };
    return styles[category] || styles.general;
  };

  // Format timestamp
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="relative">
      {/* Notification Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-full hover:bg-gray-100 transition-colors"
      >
        <Bell size={24} className="text-gray-700" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[600px] flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold">Notifications</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <X size={20} />
              </button>
            </div>

            {/* Filters */}
            <div className="flex gap-2">
              <button
                onClick={() => setFilter('all')}
                className={`px-3 py-1 rounded text-sm ${
                  filter === 'all'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilter('unread')}
                className={`px-3 py-1 rounded text-sm ${
                  filter === 'unread'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                Unread
              </button>
              <button
                onClick={() => setFilter('read')}
                className={`px-3 py-1 rounded text-sm ${
                  filter === 'read'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                Read
              </button>
            </div>
          </div>

          {/* Actions */}
          {notifications.length > 0 && (
            <div className="px-4 py-2 border-b border-gray-200 flex gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  Mark all read
                </button>
              )}
              <button
                onClick={clearReadNotifications}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Clear read
              </button>
            </div>
          )}

          {/* Notification List */}
          <div className="overflow-y-auto flex-1">
            {loading ? (
              <div className="p-8 text-center text-gray-500">
                Loading notifications...
              </div>
            ) : error ? (
              <div className="p-8 text-center text-red-500">
                Error: {error}
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <Bell size={48} className="mx-auto mb-2 text-gray-300" />
                <p>No notifications</p>
              </div>
            ) : (
              notifications.map((notification) => {
                const categoryStyle = getCategoryStyle(notification.category);
                return (
                  <div
                    key={notification.id}
                    className={`p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                      !notification.is_read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex gap-3">
                      {/* Category Icon */}
                      <div
                        className={`flex-shrink-0 w-10 h-10 rounded-full ${categoryStyle.bg} flex items-center justify-center text-xl`}
                      >
                        {categoryStyle.icon}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <h4 className="font-semibold text-sm text-gray-900 line-clamp-1">
                            {notification.title}
                          </h4>
                          {!notification.is_read && (
                            <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full mt-1" />
                          )}
                        </div>

                        <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                          {notification.message}
                        </p>

                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-500">
                            {formatTime(notification.created_at)}
                          </span>

                          <div className="flex gap-2">
                            {!notification.is_read && (
                              <button
                                onClick={() => markAsRead(notification.id)}
                                className="text-blue-600 hover:text-blue-800"
                                title="Mark as read"
                              >
                                <Check size={16} />
                              </button>
                            )}
                            <button
                              onClick={() => deleteNotification(notification.id)}
                              className="text-red-600 hover:text-red-800"
                              title="Delete"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>

                        {/* Category Badge */}
                        <span
                          className={`inline-block mt-2 px-2 py-1 rounded text-xs ${categoryStyle.bg} ${categoryStyle.text}`}
                        >
                          {notification.category_display}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;

// Usage Example:
// import NotificationCenter from './NotificationCenter';
//
// function App() {
//   const [token, setToken] = useState(localStorage.getItem('access_token'));
//
//   return (
//     <div className="app">
//       <nav className="navbar">
//         <NotificationCenter 
//           token={token}
//           apiBaseUrl="http://localhost:8000/api"
//         />
//       </nav>
//     </div>
//   );
// }
