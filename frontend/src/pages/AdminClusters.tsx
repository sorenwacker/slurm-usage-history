import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminClient, type Cluster } from '../api/adminClient';
import './AdminClusters.css';

export function AdminClusters() {
  const [clusters, setClusters] = useState<Cluster[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [rotatingKey, setRotatingKey] = useState<string | null>(null);
  const [newAPIKey, setNewAPIKey] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!adminClient.isAuthenticated()) {
      navigate('/admin/login');
      return;
    }

    loadClusters();
  }, [navigate]);

  const loadClusters = async () => {
    try {
      const data = await adminClient.getClusters();
      setClusters(data.clusters);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load clusters');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    adminClient.logout();
    navigate('/admin/login');
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete cluster "${name}"?`)) {
      return;
    }

    try {
      await adminClient.deleteCluster(id);
      await loadClusters();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete cluster');
    }
  };

  const handleToggleActive = async (cluster: Cluster) => {
    try {
      await adminClient.updateCluster(cluster.id, { active: !cluster.active });
      await loadClusters();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update cluster');
    }
  };

  const handleRotateKey = async (clusterId: string) => {
    if (!confirm('Are you sure you want to rotate the API key? The old key will be immediately invalidated.')) {
      return;
    }

    try {
      setRotatingKey(clusterId);
      const result = await adminClient.rotateAPIKey(clusterId);
      setNewAPIKey(result.new_api_key);
      await loadClusters();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rotate API key');
    } finally {
      setRotatingKey(null);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="clusters-container">
        <div className="clusters-loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="clusters-container">
      {/* Header */}
      <div className="clusters-header">
        <div className="clusters-header-content">
          <div className="clusters-header-title">
            <h1>Cluster Management</h1>
            <p className="clusters-header-subtitle">Manage SLURM clusters and API keys</p>
          </div>
          <div className="clusters-header-nav">
            <a href="/">Dashboard</a>
            <a href="/admin/config">YAML Config</a>
            <a href="/admin/users">Users</a>
            <button onClick={handleLogout}>Logout</button>
          </div>
        </div>
      </div>

      <div className="clusters-content">
        {/* Error Message */}
        {error && (
          <div className="clusters-error">
            <div className="clusters-error-text">{error}</div>
            <button onClick={() => setError('')} className="clusters-error-close">
              ×
            </button>
          </div>
        )}

        {/* New API Key Modal */}
        {newAPIKey && (
          <div className="clusters-modal-overlay">
            <div className="clusters-modal">
              <h3 className="clusters-modal-title">New API Key Generated</h3>
              <p className="clusters-modal-text">
                This is the only time the full key will be shown. Copy it now and update your cluster configuration.
              </p>
              <div className="clusters-modal-code">
                <code>{newAPIKey}</code>
              </div>
              <div className="clusters-modal-actions">
                <button
                  onClick={() => copyToClipboard(newAPIKey)}
                  className="clusters-form-submit"
                >
                  Copy to Clipboard
                </button>
                <button
                  onClick={() => setNewAPIKey(null)}
                  className="clusters-form-cancel"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="clusters-actions">
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="clusters-btn-primary"
          >
            {showCreateForm ? 'Cancel' : '+ Add Cluster'}
          </button>
        </div>

        {/* Create Form */}
        {showCreateForm && (
          <CreateClusterForm
            onSuccess={() => {
              setShowCreateForm(false);
              loadClusters();
            }}
            onCancel={() => setShowCreateForm(false)}
            onAPIKeyGenerated={(key) => setNewAPIKey(key)}
          />
        )}

        {/* Clusters List */}
        <div className="clusters-table-container">
          <table className="clusters-table">
            <thead>
              <tr>
                <th>Cluster</th>
                <th>Status</th>
                <th>Statistics</th>
                <th>API Key</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {clusters.length === 0 ? (
                <tr>
                  <td colSpan={5} className="clusters-table-empty">
                    No clusters yet. Click "Add Cluster" to get started.
                  </td>
                </tr>
              ) : (
                clusters.map((cluster) => (
                  <tr key={cluster.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{cluster.name}</div>
                      {cluster.description && (
                        <div style={{ fontSize: '0.8125rem', color: '#6c757d' }}>{cluster.description}</div>
                      )}
                      {cluster.contact_email && (
                        <div style={{ fontSize: '0.75rem', color: '#adb5bd' }}>{cluster.contact_email}</div>
                      )}
                    </td>
                    <td>
                      <span className={`clusters-badge ${cluster.active ? 'clusters-badge-active' : 'clusters-badge-inactive'}`}>
                        {cluster.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div>Jobs: {cluster.total_jobs_submitted.toLocaleString()}</div>
                      <div style={{ fontSize: '0.75rem', color: '#6c757d' }}>Last: {formatDate(cluster.last_submission)}</div>
                    </td>
                    <td>
                      <div className="clusters-api-key">
                        <code>{cluster.api_key.substring(0, 16)}...</code>
                        <button
                          onClick={() => copyToClipboard(cluster.api_key)}
                          className="clusters-copy-btn"
                          title="Copy full API key"
                        >
                          📋
                        </button>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#adb5bd', marginTop: '0.25rem' }}>
                        Created: {new Date(cluster.api_key_created).toLocaleDateString()}
                      </div>
                    </td>
                    <td>
                      <div className="clusters-actions-menu">
                        <a
                          href={`/admin/config?cluster=${cluster.name}`}
                          className="clusters-action-btn action-secondary"
                          style={{ textDecoration: 'none' }}
                        >
                          Configure
                        </a>
                        <button
                          onClick={() => handleToggleActive(cluster)}
                          className="clusters-action-btn action-primary"
                        >
                          {cluster.active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          onClick={() => handleRotateKey(cluster.id)}
                          disabled={rotatingKey === cluster.id}
                          className="clusters-action-btn action-warning"
                        >
                          {rotatingKey === cluster.id ? 'Rotating...' : 'Rotate Key'}
                        </button>
                        <button
                          onClick={() => handleDelete(cluster.id, cluster.name)}
                          className="clusters-action-btn action-danger"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

interface CreateClusterFormProps {
  onSuccess: () => void;
  onCancel: () => void;
  onAPIKeyGenerated: (key: string) => void;
}

function CreateClusterForm({ onSuccess, onCancel, onAPIKeyGenerated }: CreateClusterFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const cluster = await adminClient.createCluster({
        name,
        description: description || undefined,
        contact_email: contactEmail || undefined,
        location: location || undefined,
      });

      onAPIKeyGenerated(cluster.api_key);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create cluster');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="clusters-form">
      <h3 className="clusters-form-title">Add New Cluster</h3>

      {error && (
        <div className="clusters-error" style={{ marginBottom: '1rem' }}>
          <div className="clusters-error-text">{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="clusters-form-group">
          <label className="clusters-form-label">
            Cluster Name *
          </label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="clusters-form-input"
            placeholder="hpc-cluster-01"
          />
          <p className="clusters-form-hint">
            Hostname or identifier for the cluster
          </p>
        </div>

        <div className="clusters-form-group">
          <label className="clusters-form-label">
            Description
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="clusters-form-input"
            placeholder="Main HPC cluster for physics department"
          />
        </div>

        <div className="clusters-form-group">
          <label className="clusters-form-label">
            Contact Email
          </label>
          <input
            type="email"
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            className="clusters-form-input"
            placeholder="admin@example.com"
          />
        </div>

        <div className="clusters-form-group">
          <label className="clusters-form-label">
            Location
          </label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="clusters-form-input"
            placeholder="Building A, Room 101"
          />
        </div>

        <div className="clusters-form-actions">
          <button
            type="submit"
            disabled={loading}
            className="clusters-form-submit"
          >
            {loading ? 'Creating...' : 'Create Cluster'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="clusters-form-cancel"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
