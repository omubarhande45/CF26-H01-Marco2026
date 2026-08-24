# Institution onboarding (simulation)

`POST /institutions` (admin) → `POST /institutions/{id}/activate`  
Activate requires health check + schema compatibility `COMPATIBLE`.  
Sample fourth schema: Research Institute (`subject` / `dx_list` / `rx_list` / `assay`). Enable with `NODE_R=http://127.0.0.1:8104`.
