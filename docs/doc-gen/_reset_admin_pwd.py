"""Reseta a senha do admin@hw1.com.br para Admin@2026 via docker exec."""
import subprocess
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
h = pwd_context.hash("Admin@2026")

sql = f"UPDATE users SET hashed_password='{h}' WHERE email='admin@hw1.com.br';"

result = subprocess.run(
    ["docker", "exec", "gaa-postgres", "psql", "-U", "gestor", "-d", "gestao_arquivistica", "-c", sql],
    capture_output=True,
    text=True,
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RC:", result.returncode)
