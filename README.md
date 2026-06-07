# drinks_to_ass_bot

Маленький Telegram-бот, который реагирует на любое сообщение, содержащее формы слова **«напитки»** (напиток, напитка, напитки, напитков, напиточек, ...), и отвечает реплаем `#вжопунапитки`.

Стек: **Python 3.12 + aiogram 3**, long-polling. Хостинг: **Oracle Cloud Always Free** (постоянно бесплатная ARM-VM с 4 vCPU + 24 ГБ RAM).

---

## Содержание

- [1. Что нужно подготовить](#1-что-нужно-подготовить)
- [2. Локальный запуск](#2-локальный-запуск)
- [3. Залить проект в GitHub](#3-залить-проект-в-github)
- [4. Поднять бесплатную VM на Oracle Cloud](#4-поднять-бесплатную-vm-на-oracle-cloud)
- [5. Деплой бота на VM](#5-деплой-бота-на-vm)
- [6. CI/CD через GitHub Actions](#6-cicd-через-github-actions)
- [7. План задач (GitHub Issues)](#7-план-задач-github-issues)
- [8. Альтернативы хостинга](#8-альтернативы-хостинга)
- [9. FAQ и траблшут](#9-faq-и-траблшут)

---

## 1. Что нужно подготовить

### 1.1. Создать бота у @BotFather

1. В Telegram открой [@BotFather](https://t.me/BotFather).
2. Команда `/newbot`, придумай имя и username (заканчивается на `_bot` или `bot`).
3. BotFather отдаст токен вида `1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA` — **сохрани**, он понадобится в `.env`.
4. Чтобы бот видел **все** сообщения в группе (не только команды `/...`), отключи Privacy Mode:
   - `/mybots` → выбери своего бота → `Bot Settings` → `Group Privacy` → `Turn off`.
5. Добавь бота в нужный групповой чат и дай права на отправку сообщений.

> ⚠️ Без отключённого Privacy Mode бот в групповом чате будет молчать.

### 1.2. Установить инструменты на свой комп

- Python 3.12+
- Git
- (опционально) Docker + Docker Compose
- (опционально) [GitHub CLI `gh`](https://cli.github.com/) — пригодится для создания репы и issues
- SSH-клиент (есть из коробки в Linux/macOS/WSL)

---

## 2. Локальный запуск

```bash
cd ~/drinks_to_ass_bot

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest ruff

cp .env.example .env
# открой .env и впиши свой BOT_TOKEN
```

Запуск:

```bash
python bot.py
```

Тесты и линт:

```bash
pytest
ruff check .
ruff format --check .
```

Альтернативно через Docker:

```bash
docker build -t drinks-bot .
docker run --rm --env-file .env drinks-bot
```

---

## 3. Залить проект в GitHub

```bash
cd ~/drinks_to_ass_bot
git init -b main
git add .
git commit -m "init: drinks_to_ass_bot"

# Вариант А — через gh CLI (быстро):
gh auth login        # если ещё не залогинен
gh repo create drinks_to_ass_bot --public --source=. --remote=origin --push

# Вариант Б — руками:
# 1) создай пустую репу на github.com (без README/license/gitignore)
# 2) затем:
git remote add origin git@github.com:<твой_логин>/drinks_to_ass_bot.git
git push -u origin main
```

После пуша зайди в **Settings → Actions → General → Workflow permissions** и убедись, что выбрано **Read and write permissions** (нужно для пуша Docker-образа в GHCR).

После первого пуша поправь строку `image:` в `docker-compose.yml` — замени `CHANGE_ME` на свой GitHub-логин в нижнем регистре.

---

## 4. Поднять бесплатную VM на Oracle Cloud

### 4.1. Регистрация

1. Зайди на [cloud.oracle.com](https://www.oracle.com/cloud/free/) → **Start for free**.
2. Понадобится карта для верификации — **деньги не спишутся**, пока сам не переключишь аккаунт на платный.
3. Выбери регион поближе с хорошей доступностью ARM Ampere: **Frankfurt**, **Amsterdam**, **Stockholm**, **US East (Ashburn)** или **US West (Phoenix)**. В Токио/Сингапуре часто «Out of capacity».

### 4.2. Создать Always Free VM

1. В консоли: **☰ Menu → Compute → Instances → Create instance**.
2. **Image**: Canonical Ubuntu 22.04 (или 24.04).
3. **Shape**: `Change shape` → вкладка **Ampere** → `VM.Standard.A1.Flex` → 1 OCPU + 6 ГБ RAM (с запасом — для бота хватит и меньшего; лимит Always Free — суммарно 4 OCPU/24 ГБ).
4. **Networking**: оставь дефолтный VCN, **Assign a public IPv4 address** = Yes.
5. **SSH keys**: загрузи свой публичный ключ (`~/.ssh/id_ed25519.pub`) или сгенерируй новый.
6. Жми **Create**. Если получишь `Out of capacity` — попробуй другой регион или повтори через час.

### 4.3. Открыть исходящий трафик (входящий для бота не нужен — мы используем long polling)

Бот сам ходит наружу к `api.telegram.org` — исходящие разрешены по умолчанию. Входящие порты открывать не нужно, **кроме SSH 22** (открыт по умолчанию для подсети `0.0.0.0/0` — для безопасности позже сузишь до своего IP).

### 4.4. Зайти на VM

```bash
ssh ubuntu@<PUBLIC_IP>
```

### 4.5. Установить Docker

```bash
sudo apt update
sudo apt -y install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

Проверь: `docker run --rm hello-world`.

### 4.6. У Ubuntu на Oracle часто закрыт iptables — открой исходящий (на всякий случай)

Oracle добавляет правило `REJECT all` в `iptables`. Для исходящих обычно ок, но если что:

```bash
sudo iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT
sudo netfilter-persistent save || sudo apt -y install iptables-persistent
```

---

## 5. Деплой бота на VM

### 5.1. Минималистичный вариант (без CI/CD, ручной)

На VM:

```bash
mkdir -p ~/drinks-to-ass-bot && cd ~/drinks-to-ass-bot
# положи сюда docker-compose.yml и .env (только BOT_TOKEN)
nano .env             # BOT_TOKEN=...
nano docker-compose.yml   # вставь содержимое, поменяй CHANGE_ME на свой github-логин
docker compose pull
docker compose up -d
docker compose logs -f
```

`restart: unless-stopped` в compose автоматически поднимет бота после ребута VM.

### 5.2. Авто-деплой с GitHub Actions

См. раздел [6. CI/CD](#6-cicd-через-github-actions).

---

## 6. CI/CD через GitHub Actions

В репе уже есть два workflow:

- `.github/workflows/ci.yml` — линт (ruff) + тесты (pytest) на каждый push/PR.
- `.github/workflows/deploy.yml` — собирает мультиплатформенный Docker-образ (amd64 + arm64), пушит в **GitHub Container Registry** (`ghcr.io`) и опционально деплоит на VM по SSH.

### 6.1. Включить публикацию образа в GHCR

1. **Settings → Actions → General → Workflow permissions** → `Read and write permissions`.
2. После первого успешного запуска `Deploy` зайди в **Packages** на странице юзера → найди свой образ `drinks_to_ass_bot` → **Package settings** → сделай публичным (иначе придётся логиниться в GHCR с VM).

### 6.2. Включить авто-деплой по SSH (опционально)

В репе **Settings → Secrets and variables → Actions**:

**Variables**:
- `DEPLOY_ENABLED` = `true`

**Secrets**:
- `SSH_HOST` — публичный IP VM
- `SSH_USER` — `ubuntu`
- `SSH_PORT` — `22` (можно не задавать)
- `SSH_PRIVATE_KEY` — приватный ключ для входа на VM (целиком, с `-----BEGIN ... KEY-----`)
- `GHCR_PULL_TOKEN` — PAT с правом `read:packages` (если образ приватный; для публичного не нужен — но secret должен существовать, оставь его пустым или выпиши шаг логина из workflow)

На VM один раз положи `docker-compose.yml` и `.env` в `~/drinks-to-ass-bot/`. Дальше каждый push в `main` будет автоматически обновлять контейнер.

---

## 7. План задач (GitHub Issues)

После того как зальёшь репу, выполни в её корне (требуется `gh` CLI):

```bash
gh issue create --title "Получить BOT_TOKEN у @BotFather и отключить Privacy Mode" \
  --body "1) /newbot в @BotFather\n2) Сохранить токен\n3) Bot Settings → Group Privacy → Turn off"

gh issue create --title "Поднять Always Free ARM VM на Oracle Cloud" \
  --body "VM.Standard.A1.Flex (Ubuntu 22.04). Регион — Frankfurt/Amsterdam/Ashburn. См. README §4."

gh issue create --title "Установить Docker на VM и задеплоить бота вручную" \
  --body "См. README §5.1. Проверить, что бот отвечает в тестовом чате."

gh issue create --title "Настроить GHCR и автодеплой по SSH" \
  --body "1) Workflow permissions = Read+Write\n2) Сделать образ публичным\n3) Завести DEPLOY_ENABLED + SSH_* секреты\n4) Проверить, что push в main обновляет контейнер."

gh issue create --title "Расширить словарь форм слова (напиточный, напиточная и т.п.)" \
  --body "Сейчас DRINKS_PATTERN покрывает базовые формы существительного. Подумать про прилагательные/уменьшительно-ласкательные."

gh issue create --title "Базовый мониторинг: healthcheck + алёрт в Telegram, если бот упал" \
  --body "Опционально. Можно сделать вторым ботом, который раз в N минут пингует первого."
```

Если `gh` не настроен — просто создай эти задачи в Issues руками, заголовки скопируй из команд выше.

---

## 8. Альтернативы хостинга

| Вариант | Плюсы | Минусы |
|---|---|---|
| **Oracle Cloud Always Free** ⭐ | 4 vCPU ARM + 24 ГБ RAM, навсегда бесплатно, полноценный VPS | Регистрация с картой, иногда «Out of capacity» по ARM |
| AWS EC2 t2.micro | Знакомая экосистема | Free Tier только 12 месяцев, дальше платно |
| AWS Lambda + webhook | Бесплатный always-free слой (1M req/мес) | Нужно переписать на webhook + API Gateway, холодные старты |
| Fly.io / Render free | Просто, push-to-deploy | Free-тарифы регулярно ужимают; могут засыпать |
| **VPS ps.kz** | Локально, быстрый пинг, оплата в тенге | Платно (~1000–2000 ₸/мес). См. ниже краткую инструкцию |

### Если решишь брать VPS на ps.kz

1. Регистрация на [ps.kz](https://www.ps.kz/) → раздел **VPS/VDS** → бери самый дешёвый тариф (1 vCPU, 1 ГБ RAM достаточно).
2. ОС: Ubuntu 22.04. После оплаты придут IP, root-пароль и доступ в панель.
3. SSH: `ssh root@<IP>`, сразу заведи юзера, отключи root-логин, поставь fail2ban, добавь свой SSH-ключ:
   ```bash
   adduser deploy
   usermod -aG sudo deploy
   mkdir -p /home/deploy/.ssh && cp ~/.ssh/authorized_keys /home/deploy/.ssh/
   chown -R deploy:deploy /home/deploy/.ssh
   sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
   systemctl restart ssh
   apt update && apt -y install fail2ban
   ```
4. Дальше **тот же процесс**, что и для Oracle: установка Docker (§4.5), `docker compose up -d` с тем же `docker-compose.yml` и `.env`.
5. В GitHub Actions просто впиши IP/юзера ps.kz в секреты — деплой-workflow одинаковый.

---

## 9. FAQ и траблшут

**Бот молчит в группе.** Проверь, что отключён Group Privacy у BotFather и бот реально добавлен в чат.

**Бот падает с `Unauthorized`.** Токен битый или попал в публичный коммит — отзови через `/revoke` у BotFather и впиши новый в `.env`.

**Oracle пишет `Out of host capacity`.** Попробуй другой регион (Frankfurt/Amsterdam/Ashburn обычно зеленее), либо запусти автоповторитель — есть готовые скрипты в Gist'ах.

**Контейнер не пуллится с GHCR на VM.** Либо сделай образ публичным в **Packages → settings**, либо логинься: `echo <PAT> | docker login ghcr.io -u <логин> --password-stdin`.

**Хочется webhook вместо polling.** Долгосрочно лучше — но нужен публичный HTTPS, домен и обратный прокси. Для 30 человек polling абсолютно ок и проще на порядок.

**Как обновить без CI/CD.** На VM: `cd ~/drinks-to-ass-bot && docker compose pull && docker compose up -d`.
