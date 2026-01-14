/**
 * ErrorBoundary.jsx
 * =================
 * React Error Boundary to catch and display component errors
 *
 * Features:
 * - Catches JavaScript errors anywhere in child component tree
 * - Logs error details to console
 * - Shows user-friendly error message
 * - Provides retry mechanism
 *
 * Author: KOMAS Team
 * Version: 4.0
 */

import React from 'react';
import { Button, Card, Alert } from './ui';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details to console
    console.error('[ErrorBoundary] ❌ Caught error:', error);
    console.error('[ErrorBoundary] Error info:', errorInfo);
    console.error('[ErrorBoundary] Component stack:', errorInfo.componentStack);

    // Store error details in state
    this.setState({
      error: error,
      errorInfo: errorInfo,
    });

    // You can also log the error to an error reporting service
    // logErrorToService(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Render fallback UI
      return (
        <div className="min-h-screen bg-dark-900 flex items-center justify-center p-4">
          <Card className="max-w-2xl w-full">
            <Card.Header className="border-b border-dark-700">
              <div className="flex items-center gap-3">
                <span className="text-4xl">💥</span>
                <div>
                  <h2 className="text-xl font-bold text-white">Ошибка приложения</h2>
                  <p className="text-sm text-gray-400 mt-1">
                    Произошла непредвиденная ошибка
                  </p>
                </div>
              </div>
            </Card.Header>

            <Card.Body className="space-y-4">
              <Alert variant="danger">
                <div className="space-y-2">
                  <p className="font-semibold">Детали ошибки:</p>
                  <div className="bg-dark-800 rounded-lg p-3 font-mono text-sm overflow-auto max-h-40">
                    {this.state.error && this.state.error.toString()}
                  </div>
                </div>
              </Alert>

              {this.state.errorInfo && (
                <div>
                  <p className="text-sm text-gray-400 mb-2">Component Stack:</p>
                  <div className="bg-dark-800 rounded-lg p-3 font-mono text-xs overflow-auto max-h-60">
                    <pre className="text-gray-300 whitespace-pre-wrap">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </div>
                </div>
              )}

              <div className="border-t border-dark-700 pt-4 mt-4">
                <p className="text-sm text-gray-400 mb-3">Что можно сделать:</p>
                <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside mb-4">
                  <li>Попробуйте перезагрузить страницу</li>
                  <li>Очистите кеш браузера (Ctrl+Shift+R)</li>
                  <li>Проверьте консоль браузера (F12) для деталей</li>
                  <li>Убедитесь, что backend сервер запущен</li>
                </ul>

                <div className="flex gap-3">
                  <Button
                    variant="primary"
                    onClick={this.handleReset}
                    className="flex-1"
                  >
                    🔄 Попробовать снова
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => window.location.reload()}
                    className="flex-1"
                  >
                    ♻️ Перезагрузить страницу
                  </Button>
                </div>
              </div>

              <div className="bg-yellow-600/10 border border-yellow-600/30 rounded-lg p-3 mt-4">
                <div className="flex items-start gap-2">
                  <span className="text-yellow-400">⚠️</span>
                  <div className="text-xs text-yellow-200">
                    <p className="font-semibold mb-1">Для разработчиков:</p>
                    <p>Откройте консоль браузера (F12) для полной трассировки ошибки</p>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </div>
      );
    }

    // No error, render children normally
    return this.props.children;
  }
}

export default ErrorBoundary;
