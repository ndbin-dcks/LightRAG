# LightRAG Deployment Modes

Hệ thống hỗ trợ 2 deployment modes: **Development** và **Production**

## 📁 Files

```
/opt/lightrag/
├── docker-compose.prod.yml    # Production mode
├── docker-compose.dev.yml     # Development mode
├── deploy.sh                  # Helper script
├── .env                       # Environment config
└── lightrag/                  # Source code (mounted trong dev mode)
```

---

## 🚀 Production Mode (Recommended cho VPS)

### **Đặc điểm:**
- ✅ Code được baked vào Docker image từ GitHub
- ✅ Ổn định, không bị ảnh hưởng bởi filesystem
- ✅ Performance tốt nhất
- ✅ Container name: `lightrag`
- ❌ Cần rebuild image để update code

### **Sử dụng:**

```bash
# Start production mode
./deploy.sh prod

# Hoặc manual:
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart
docker compose -f docker-compose.prod.yml restart

# Stop
docker compose -f docker-compose.prod.yml down
```

### **Update code trong Production:**

```bash
# 1. Commit & push to GitHub
cd /opt/lightrag
git add .
git commit -m "feat: your changes"
git push origin main

# 2. Đợi GitHub Actions build image (~2-3 phút)

# 3. Pull image mới và restart
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# Hoặc dùng script:
./deploy.sh prod
```

---

## 🔧 Development Mode (Cho testing nhanh)

### **Đặc điểm:**
- ✅ Code mount từ `/opt/lightrag/lightrag/`
- ✅ Sửa code → restart → có hiệu lực ngay
- ✅ Không cần rebuild image
- ✅ Container name: `lightrag-dev`
- ✅ Debug mode enabled
- ⚠️ Performance hơi chậm hơn production
- ⚠️ CHỈ dùng để test, KHÔNG deploy production lâu dài

### **Sử dụng:**

```bash
# Start development mode
./deploy.sh dev

# Hoặc manual:
docker compose -f docker-compose.dev.yml up -d

# View logs
docker compose -f docker-compose.dev.yml logs -f

# Restart (sau khi sửa code)
docker compose -f docker-compose.dev.yml restart

# Stop
docker compose -f docker-compose.dev.yml down
```

### **Workflow trong Development:**

```bash
# 1. Sửa code
nano /opt/lightrag/lightrag/api/lightrag_server.py

# 2. Restart container
docker compose -f docker-compose.dev.yml restart

# 3. Test ngay - code changes có hiệu lực!

# 4. Khi đã OK, commit & push
git add .
git commit -m "feat: tested changes"
git push origin main

# 5. Switch về production mode
./deploy.sh prod
```

---

## 📊 Check Status

```bash
# Dùng script
./deploy.sh status

# Manual
docker ps -a | grep lightrag
```

**Output:**
```
✅ DEVELOPMENT mode active (lightrag-dev)
   Code mounted from: /opt/lightrag/lightrag/

hoặc

✅ PRODUCTION mode active (lightrag)
   Code from image: ghcr.io/hkuds/lightrag:latest
```

---

## 🔄 Switch Between Modes

### **Dev → Prod:**
```bash
./deploy.sh prod
# Script tự động stop dev container và start prod container
```

### **Prod → Dev:**
```bash
./deploy.sh dev
# Script tự động stop prod container và start dev container
```

---

## ⚠️ Important Notes

### **1. Code Sync:**
- Development mode: Sửa `/opt/lightrag/lightrag/` → restart → OK
- Production mode: Sửa code → push GitHub → CI/CD → pull image → restart

### **2. Data Persistence:**
- Cả 2 modes đều dùng **CÙNG data volumes**
- PostgreSQL data: `postgres_data` volume
- RAG storage: `./data/rag_storage/`
- Không mất data khi switch modes

### **3. Container Names:**
- Production: `lightrag` (port 9621)
- Development: `lightrag-dev` (port 9621)
- **KHÔNG chạy cả 2 cùng lúc** (conflict port 9621)

### **4. Best Practices:**
```
✅ Development: Test tính năng mới, debug nhanh
✅ Production: Deploy ổn định, code từ GitHub

❌ Không sửa code trực tiếp trong container (/app/lightrag/)
❌ Không để dev mode chạy lâu dài trên production VPS
```

---

## 🎯 Recommended Workflow

### **Khi Develop Tính Năng Mới:**
```bash
1. ./deploy.sh dev              # Switch to dev mode
2. Edit code trong /opt/lightrag/lightrag/
3. docker compose -f docker-compose.dev.yml restart
4. Test & debug
5. Repeat steps 2-4 until OK
6. git commit & push
7. ./deploy.sh prod             # Switch back to production
```

### **Khi Deploy Production:**
```bash
1. Ensure all changes committed to GitHub
2. ./deploy.sh prod
3. Monitor logs: docker compose -f docker-compose.prod.yml logs -f
```

### **Khi Có Bug Cần Fix Gấp:**
```bash
1. ./deploy.sh dev              # Quick switch to dev
2. Fix bug trong /opt/lightrag/lightrag/
3. Restart & test
4. Commit & push fix
5. ./deploy.sh prod             # Deploy fixed version
```

---

## 📚 Additional Commands

### **View logs:**
```bash
# Production
docker compose -f docker-compose.prod.yml logs -f lightrag

# Development
docker compose -f docker-compose.dev.yml logs -f lightrag
```

### **Exec vào container:**
```bash
# Production
docker exec -it lightrag bash

# Development
docker exec -it lightrag-dev bash
```

### **Check HiRAG status:**
```bash
docker exec -it lightrag python3 -c "from lightrag.hierarchical import HierarchicalExtension; print('✅ OK')"
```

---

## 🆘 Troubleshooting

### **Port conflict:**
```bash
# Stop all lightrag containers
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.prod.yml down

# Start desired mode
./deploy.sh prod  # hoặc ./deploy.sh dev
```

### **Code changes không có hiệu lực:**
```bash
# Check mode đang chạy
./deploy.sh status

# Nếu production mode: cần push GitHub & pull image
# Nếu development mode: chỉ cần restart
```

### **Container không start:**
```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check PostgreSQL
docker ps -a | grep postgres
```

---

**Created:** 2025-12-13  
**Author:** Claude Assistant  
**Purpose:** Hướng dẫn sử dụng dev/prod deployment modes cho LightRAG
