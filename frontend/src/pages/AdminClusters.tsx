import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminClient, type Cluster } from '../api/adminClient';

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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Cluster Management</h1>
              <p className="text-sm text-gray-600">Manage SLURM clusters and API keys</p>
            </div>
            <div className="flex space-x-4">
              <a
                href="/"
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Dashboard
              </a>
              <button
                onClick={handleLogout}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error Message */}
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">{error}</h3>
              </div>
              <div className="ml-auto pl-3">
                <button
                  onClick={() => setError('')}
                  className="text-red-800 hover:text-red-600"
                >
                  ×
                </button>
              </div>
            </div>
          </div>
        )}

        {/* New API Key Modal */}
        {newAPIKey && (
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg p-6 max-w-lg w-full">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                New API Key Generated
              </h3>
              <p className="text-sm text-gray-600 mb-4">
                This is the only time the full key will be shown. Copy it now and update your cluster configuration.
              </p>
              <div className="bg-gray-50 p-3 rounded border border-gray-200 mb-4">
                <code className="text-sm break-all">{newAPIKey}</code>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => copyToClipboard(newAPIKey)}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Copy to Clipboard
                </button>
                <button
                  onClick={() => setNewAPIKey(null)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="mb-6">
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
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
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cluster
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Statistics
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  API Key
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {clusters.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    No clusters yet. Click "Add Cluster" to get started.
                  </td>
                </tr>
              ) : (
                clusters.map((cluster) => (
                  <tr key={cluster.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{cluster.name}</div>
                      {cluster.description && (
                        <div className="text-sm text-gray-500">{cluster.description}</div>
                      )}
                      {cluster.contact_email && (
                        <div className="text-xs text-gray-400">{cluster.contact_email}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          cluster.active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {cluster.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>Jobs: {cluster.total_jobs_submitted.toLocaleString()}</div>
                      <div className="text-xs">Last: {formatDate(cluster.last_submission)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center space-x-2">
                        <code className="text-xs">{cluster.api_key.substring(0, 16)}...</code>
                        <button
                          onClick={() => copyToClipboard(cluster.api_key)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Copy full API key"
                        >
                          📋
                        </button>
                      </div>
                      <div className="text-xs text-gray-400">
                        Created: {new Date(cluster.api_key_created).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex flex-col space-y-1">
                        <button
                          onClick={() => handleToggleActive(cluster)}
                          className="text-blue-600 hover:text-blue-900 text-left"
                        >
                          {cluster.active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          onClick={() => handleRotateKey(cluster.id)}
                          disabled={rotatingKey === cluster.id}
                          className="text-yellow-600 hover:text-yellow-900 text-left disabled:opacity-50"
                        >
                          {rotatingKey === cluster.id ? 'Rotating...' : 'Rotate Key'}
                        </button>
                        <button
                          onClick={() => handleDelete(cluster.id, cluster.name)}
                          className="text-red-600 hover:text-red-900 text-left"
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
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Cluster</h3>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-3">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Cluster Name *
          </label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="hpc-cluster-01"
          />
          <p className="mt-1 text-sm text-gray-500">
            Hostname or identifier for the cluster
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Description
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="Main HPC cluster for physics department"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Contact Email
          </label>
          <input
            type="email"
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="admin@example.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Location
          </label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="Building A, Room 101"
          />
        </div>

        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Cluster'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
