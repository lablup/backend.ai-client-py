Add support for storage proxy
- The vfolder upload and download functions/commands now uses the storage proxy designated by the gateway APIs with the issued JWT token to transfer actual payloads.
- The vfolder upload function uses `aiotusclient` for large-sized, resumable uploads.
