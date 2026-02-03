import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="p-4 m-4 bg-red-950/50 border border-red-900 rounded text-red-200">
          <h2 className="text-lg font-bold mb-2">Something went wrong</h2>
          <p className="text-sm mb-2">The application encountered an error rendering this component.</p>
          {this.state.error && (
            <pre className="bg-black/50 p-2 rounded text-xs overflow-auto max-h-40">
              {this.state.error.toString()}
            </pre>
          )}
          <button
            className="mt-4 px-4 py-2 bg-red-800 hover:bg-red-700 rounded text-sm font-bold"
            onClick={() => this.setState({ hasError: false })}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
