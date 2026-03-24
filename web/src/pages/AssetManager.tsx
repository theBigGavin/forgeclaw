import { useEffect, useState } from 'react'
import {
  Upload,
  FileText,
  Image,
  Music,
  Video,
  Archive,
  Folder,
  Share2,
  Trash2,
} from 'lucide-react'
import { assetsApi } from '../api/client'
import type { Asset } from '../types'
import toast from 'react-hot-toast'

const iconMap: Record<string, React.ReactNode> = {
  text: <FileText className="w-8 h-8 text-blue-500" />,
  image: <Image className="w-8 h-8 text-green-500" />,
  audio: <Music className="w-8 h-8 text-purple-500" />,
  video: <Video className="w-8 h-8 text-red-500" />,
  code: <FileText className="w-8 h-8 text-yellow-500" />,
  binary: <Archive className="w-8 h-8 text-gray-500" />,
  directory: <Folder className="w-8 h-8 text-orange-500" />,
}

export default function AssetManager() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    loadAssets()
  }, [])

  const loadAssets = async () => {
    try {
      const response = await assetsApi.list()
      setAssets(response.data)
    } catch (error) {
      toast.error('Failed to load assets')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setUploading(true)
    try {
      await assetsApi.upload(files[0])
      toast.success('Asset uploaded!')
      loadAssets()
    } catch (error) {
      toast.error('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (assetId: string) => {
    if (!confirm('Are you sure you want to delete this asset?')) return

    try {
      await assetsApi.delete(assetId)
      setAssets(assets.filter((a) => a.id !== assetId))
      setSelectedAsset(null)
      toast.success('Asset deleted')
    } catch (error) {
      toast.error('Failed to delete asset')
    }
  }

  const handleShare = async (assetId: string, targetProjectId: string) => {
    try {
      await assetsApi.share(assetId, targetProjectId)
      toast.success('Asset shared!')
    } catch (error) {
      toast.error('Failed to share asset')
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Assets</h2>
          <p className="text-gray-500">Manage files, documents, and media</p>
        </div>
        <label className="btn-primary flex items-center gap-2 cursor-pointer">
          <Upload className="w-5 h-5" />
          {uploading ? 'Uploading...' : 'Upload'}
          <input
            type="file"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading}
          />
        </label>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Asset List */}
        <div className="col-span-2 card p-4">
          {assets.length === 0 ? (
            <div className="text-center py-12">
              <Folder className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">No assets yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              {assets.map((asset) => (
                <button
                  key={asset.id}
                  onClick={() => setSelectedAsset(asset)}
                  className={`p-4 rounded-lg border-2 text-left transition-colors ${
                    selectedAsset?.id === asset.id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-100 hover:border-gray-200'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {iconMap[asset.asset_type] || iconMap.binary}
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">
                        {asset.name}
                      </p>
                      <p className="text-sm text-gray-500">
                        v{asset.current_version}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(asset.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Asset Details */}
        <div className="card p-4">
          {selectedAsset ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3 pb-4 border-b">
                {iconMap[selectedAsset.asset_type] || iconMap.binary}
                <div>
                  <h3 className="font-semibold">{selectedAsset.name}</h3>
                  <p className="text-sm text-gray-500">{selectedAsset.asset_type}</p>
                </div>
              </div>

              <div className="space-y-3">
                <div>
                  <span className="text-xs text-gray-500 uppercase">Version</span>
                  <p className="font-medium">{selectedAsset.current_version}</p>
                </div>
                <div>
                  <span className="text-xs text-gray-500 uppercase">Created</span>
                  <p className="font-medium">
                    {new Date(selectedAsset.created_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-gray-500 uppercase">Modified</span>
                  <p className="font-medium">
                    {new Date(selectedAsset.updated_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-gray-500 uppercase">Project</span>
                  <p className="font-medium">{selectedAsset.project_id}</p>
                </div>
              </div>

              <div className="pt-4 border-t space-y-2">
                <button
                  onClick={() => handleShare(selectedAsset.id, 'other-project')}
                  className="btn-secondary w-full flex items-center justify-center gap-2"
                >
                  <Share2 className="w-4 h-4" />
                  Share
                </button>
                <button
                  onClick={() => handleDelete(selectedAsset.id)}
                  className="btn-secondary w-full flex items-center justify-center gap-2 text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              <Folder className="w-12 h-12 mx-auto mb-3" />
              <p>Select an asset to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
