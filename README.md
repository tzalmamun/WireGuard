# TZ WireGuard

একটি ছোট, সহজ WireGuard VPN সার্ভার আর অ্যাডমিন প্যানেল। নতুন VPS-এ `git clone` করে **কয়েকটি কমান্ডে** চালু করুন, প্যানেলে নাম লিখে ইউজার বানান, আর WireGuard কনফিগ (ফাইল, QR বা টেক্সট) VPN অ্যাপে দিয়ে দিন।

- **প্রতি ইউজারের জন্য ঐচ্ছিক ডাটা লিমিট (GB) ও মেয়াদ।** কিছু না দিলে ইউজার আনলিমিটেড।
- প্যানেল শুধু Python স্ট্যান্ডার্ড লাইব্রেরিতে লেখা, একটি ফাইল (`app.py`)।
- লাইট ডিজাইন, TZ ব্র্যান্ডিং, মোবাইলে সহজে চলে।

## কী কী পাবেন
- পাসওয়ার্ড দিয়ে অ্যাডমিন লগইন (HTTPS, সেলফ-সাইনড সার্টিফিকেট)
- নতুন ইউজার তৈরি, Disable / Enable / Delete
- **ইউজার বানানোর সময়ই GB লিমিট ও মেয়াদ (দিন) দেওয়া যায়, পরেও বদলানো যায়**
- সীমা পেরোলে ইউজার নিজে থেকে বন্ধ হয়ে যায় (ডাটা শেষ বা মেয়াদ শেষ)
- প্রতি ইউজারের জন্য: কনফিগ টেক্সট, **Download .conf**, Copy বাটন, QR কোড, ঠিকানা, কী ও এন্ডপয়েন্টের বিস্তারিত
- কে অনলাইন, শেষ হ্যান্ডশেক, কত ডাটা ব্যবহার হলো তা দেখা
- রিস্টার্ট বা রিবুটের পর ইউজার, টানেল ও ব্যবহৃত ডাটার হিসাব নিজে ফিরে আসে

## পুরো ছবিটা (আগে এটা বুঝে নিন)
- **সার্ভার = Linux VPS** (Ubuntu/Debian)। TZ-WG এখানেই বসে। Windows সার্ভারে এই সার্ভার বসানো যায় না।
- **ক্লায়েন্ট = আপনার ডিভাইস**: Android, iPhone, Windows 10/11, **Windows Server 2022**, macOS, Linux। ক্লায়েন্টে শুধু WireGuard অ্যাপ লাগে (নিচে বিস্তারিত)।

---

## ধাপ ১: VPS নেওয়া
- OS: **Ubuntu 22.04 / 24.04** অথবা Debian 11/12। (Ubuntu 20.04 ও চলে)
- ভার্চুয়ালাইজেশন **KVM** হতে হবে। OpenVZ/LXC ধরনের VPS-এ WireGuard চলে না, কিনে নেওয়ার আগে প্রোভাইডারকে জিজ্ঞেস করুন।
- root অ্যাক্সেস লাগবে। প্রোভাইডার ইমেইল/ড্যাশবোর্ডে **IP**, **username (সাধারণত root)** ও **পাসওয়ার্ড** দেয়, সেগুলো রাখুন।
- মেমরি 512 MB হলেই চলে।

## ধাপ ২: SSH দিয়ে VPS-এ ঢোকা

### Windows 10/11 / Windows Server 2022 থেকে
1. Start চেপে **PowerShell** বা **Command Prompt** খুলুন। (Windows-এ OpenSSH আগে থেকেই থাকে।)
2. লিখুন (`VPS_IP` এর জায়গায় আপনার VPS-এর IP):
```
ssh root@VPS_IP
```
3. প্রথমবার `Are you sure you want to continue connecting (yes/no)?` আসবে। `yes` লিখে Enter দিন।
4. **Password** চাইলে পাসওয়ার্ড টাইপ বা পেস্ট করুন। টাইপ করার সময় স্ক্রিনে কিছুই দেখা যায় না, এটাই নিয়ম। শেষে Enter চাপুন।
5. `root@...:~#` দেখা গেলে ঢুকে গেছেন।

### macOS / Linux থেকে
টার্মিনালে একই কমান্ড: `ssh root@VPS_IP`

### মোবাইল থেকে
Termius অ্যাপে নতুন Host বানিয়ে IP, username ও পাসওয়ার্ড দিন।

### PuTTY দিয়ে (ঐচ্ছিক)
PuTTY খুলে **Host Name** ঘরে IP, **Port** 22 দিয়ে Open চাপুন। এরপর `login as:` এ `root` ও পাসওয়ার্ড দিন।

### কিছু বিশেষ অবস্থা
- **SSH পোর্ট 22 না হলে:** `ssh -p পোর্ট root@VPS_IP`
- **root দেয়নি, অন্য ইউজার দিয়েছে** (যেমন `ubuntu`): `ssh ubuntu@VPS_IP` দিয়ে ঢুকে `sudo -i` চালালে root হয়ে যাবেন।
- **`Connection timed out`:** IP ঠিক আছে কি না, VPS চালু আছে কি না এবং প্রোভাইডারের ফায়ারওয়ালে TCP 22 খোলা আছে কি না দেখুন।
- **`WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED`:** একই IP-তে VPS রিইনস্টল করলে আসে। পুরনো এন্ট্রি মুছুন: `ssh-keygen -R VPS_IP`
- বের হতে: `exit`

## ধাপ ৩: পোর্ট খোলা (খুব গুরুত্বপূর্ণ)
দুটি পোর্ট খুলতে হবে:

| পোর্ট | ধরন | কাজ |
|---|---|---|
| **51820** | **UDP** | WireGuard VPN |
| **4444** | **TCP** | অ্যাডমিন প্যানেল |

আর SSH-এর জন্য **22 (TCP)** তো খোলা থাকতেই হবে।

> UDP ও TCP আলাদা জিনিস। 51820 **UDP** হিসেবে না খুললে VPN কানেক্ট হবে না।

### (ক) প্রোভাইডারের ফায়ারওয়াল (ওয়েব ড্যাশবোর্ডে)
বেশিরভাগ প্রোভাইডারের নিজস্ব ফায়ারওয়াল থাকে। সেখানে **Inbound** নিয়মে এই দুটি যোগ করুন (Source = `0.0.0.0/0` বা Anywhere):

| প্রোভাইডার | কোথায় |
|---|---|
| AWS (EC2 / Lightsail) | Security Groups বা Lightsail → Networking → Firewall |
| Google Cloud | VPC network → Firewall → Create firewall rule |
| Oracle Cloud | VCN → Security Lists (বা NSG) → Add Ingress Rules (নিচের Oracle নোটও দেখুন) |
| DigitalOcean | Networking → Firewalls |
| Hetzner | Firewalls (প্রজেক্ট থেকে) |
| Vultr | Products → Firewall |
| Contabo ও অনেক লোকাল/BDIX VPS | সাধারণত আলাদা ফায়ারওয়াল নেই। কিছু করতে হয় না |

প্যানেল শুধু নিজের IP থেকে খুলতে চাইলে 4444-এর Source এ আপনার IP দিন (সবচেয়ে নিরাপদ)।

### (খ) VPS-এর ভেতরের ফায়ারওয়াল (ufw)
SSH দিয়ে ঢুকে দেখুন ufw চালু কি না:
```
ufw status
```
`inactive` লিখলে কিছু করতে হবে না। `active` হলে **আগে SSH খুলে** তারপর বাকি দুটি খুলুন (উল্টো করলে নিজেই বাইরে আটকে যেতে পারেন):
```
ufw allow 22/tcp
ufw allow 51820/udp
ufw allow 4444/tcp
ufw reload
```
পোর্ট বদলালে সেই নম্বর দিন।

### (গ) Oracle Cloud নোট
Oracle-এর Ubuntu ইমেজে ভেতরে iptables নিয়ম থাকে যা বাইরের পোর্ট আটকে দেয়। ড্যাশবোর্ডে পোর্ট খুললেও কাজ না হলে VPS-এ চালান:
```
iptables -I INPUT -p udp --dport 51820 -j ACCEPT
iptables -I INPUT -p tcp --dport 4444 -j ACCEPT
apt install -y iptables-persistent
netfilter-persistent save
```

## ধাপ ৪: ইনস্টল (git clone দিয়ে)
প্রতিটি নতুন VPS-এ SSH দিয়ে ঢুকে এই কমান্ডগুলো একটার পর একটা চালান।

**১. git ও Docker ইনস্টল (একবারই লাগে):**
```
apt update && apt install -y git curl
curl -fsSL https://get.docker.com | sh
```

**২. ক্লোন করে ঢুকুন:**
```
git clone https://github.com/tzalmamun/WireGuard.git
cd WireGuard
```

**৩. কনফিগ ফাইল বানান ও পাসওয়ার্ড বদলান:**
```
cp .env.example .env
nano .env
```
`ADMIN_PASSWORD=` এর পরে নিজের পাসওয়ার্ড লিখুন (কমপক্ষে ৮ অক্ষর, স্পেস না দেওয়াই ভালো)। সেভ করতে **Ctrl+O**, Enter, তারপর বের হতে **Ctrl+X**। বাকি লাইনে সাধারণত হাত দিতে হয় না। `SERVER_HOST` ফাঁকা রাখলে VPS-এর IP নিজে শনাক্ত হয়।

**৪. চালু করুন (প্রথমবার কয়েক মিনিট লাগে):**
```
docker compose up -d --build
```

**৫. দেখুন চলছে কি না:**
```
docker compose ps
```
`tz-wg` এর পাশে `running` / `Up` দেখালে ঠিক আছে।

## ধাপ ৫: প্রথমবার ব্যবহার
1. ব্রাউজারে `https://VPS_IP:4444` খুলুন। সার্টিফিকেটের সতর্কতা এলে **Advanced → Continue** চাপুন (সেলফ-সাইনড সার্টিফিকেট বলে আসে)।
2. `.env`-এ দেওয়া পাসওয়ার্ড দিয়ে লগইন করুন। ফাইলে না দিলে ডিফল্ট পাসওয়ার্ড `tzalmamun` চলে, সেটা অবশ্যই বদলে নিন (নিচে দেখুন)।
3. **Create new user** ঘরে:
   - **User name** লিখুন (ইংরেজি অক্ষর, সংখ্যা, `_ . -`)
   - **Data limit in GB** এ GB লিখুন, যেমন `10` বা `2.5`। ফাঁকা রাখলে আনলিমিটেড
   - **Valid for days** এ দিন লিখুন, যেমন `30`। ফাঁকা রাখলে মেয়াদ নেই
   - **Create** চাপুন
4. ইউজারের পেজ থেকে **Download .conf** চাপুন, অথবা QR স্ক্যান করুন, অথবা **Copy** করে টেক্সট নিন।
5. WireGuard অ্যাপে ইমপোর্ট করে চালু করুন (পরের অংশ)।

> ডাউনলোড করা ফাইলের নাম `.txt` হয়ে গেলে নাম বদলে `.conf` করে নিন।

## ডাটা লিমিট ও মেয়াদ কীভাবে কাজ করে
- ইউজারের পেজে **Limits** বক্সে **Data limit (GB)** ও **Valid until (date)** বদলে **Save limits** চাপুন। ঘর ফাঁকা রাখলে ওই সীমা থাকে না।
- **ব্যবহার = ডাউনলোড + আপলোড**, দুটো মিলিয়ে গোনা হয়।
- সার্ভার প্রতি ~২০ সেকেন্ডে হিসাব দেখে। ডাটা শেষ বা মেয়াদ শেষ হলে ইউজার **নিজে থেকে বন্ধ** হয়ে যায় এবং তালিকায় `limit reached` বা `expired` দেখায়।
- মেয়াদ নির্বাচিত তারিখের **রাত ১১:৫৯** পর্যন্ত। সময় গোনা হয় UTC + `TZ_OFFSET_HOURS` (ডিফল্ট `6` = বাংলাদেশ সময়)।
- বন্ধ হওয়া ইউজারকে **আবার চালু করতে** লিমিট বাড়ান, মেয়াদ বাড়ান, অথবা **Reset used data to 0** চাপুন। যে ইউজার ডাটা/মেয়াদের কারণে বন্ধ হয়েছিল, সে এগুলো করলেই নিজে থেকে চালু হয়ে যায়।
- আপনি নিজে **Disable** করলে ইউজার বন্ধই থাকে, লিমিট বদলালেও আপনা-আপনি চালু হয় না।
- সীমা পেরোলে বন্ধ হওয়ার আগে কয়েক সেকেন্ডের সামান্য ডাটা বাড়তি যেতে পারে।
- রিস্টার্ট বা রিবুটেও ব্যবহৃত ডাটার হিসাব হারায় না।
- আগের সংস্করণে বানানো ইউজারদের কিছু না দিলে আনলিমিটেড থাকে।

---

## ক্লায়েন্টে ব্যবহার

### Android / iPhone
1. Play Store / App Store থেকে **WireGuard** অ্যাপ নিন।
2. অ্যাপে **+** চেপে **Scan from QR code** দিয়ে প্যানেলের QR স্ক্যান করুন (বা `.conf` ফাইল ইমপোর্ট করুন)।
3. টানেলের সুইচ অন করুন।

### Windows 10 / 11
1. https://www.wireguard.com/install/ থেকে Windows ইনস্টলার নামিয়ে ইনস্টল করুন।
2. **Import tunnel(s) from file** চাপুন, প্যানেল থেকে নামানো `.conf` ফাইল বাছুন।
3. **Activate** চাপুন।

### Windows Server 2022

১. **WireGuard ইনস্টল:**
- সার্ভারের ব্রাউজারে https://www.wireguard.com/install/ থেকে Windows ইনস্টলার নামান।
- ডাউনলোড আটকে গেলে (Server-এ ব্রাউজারের নিরাপত্তা সেটিং আটকায়) **PowerShell (Run as administrator)** এ:
```
Invoke-WebRequest https://download.wireguard.com/windows-client/wireguard-installer.exe -OutFile $env:TEMP\wg-installer.exe
& $env:TEMP\wg-installer.exe
```

২. **কনফিগ ফাইল সার্ভারে আনা** (যেকোনো একটি):
- সার্ভারের ব্রাউজারেই `https://VPS_IP:4444` খুলে লগইন করে **Download .conf** চাপুন।
- অথবা নিজের পিসি থেকে ফাইলটি RDP-তে কপি-পেস্ট করুন।
- অথবা প্যানেলের **Copy** দিয়ে টেক্সট নিয়ে Notepad-এ পেস্ট করে **Save as → All files** ধরনে `tz1.conf` নামে সেভ করুন। নাম ছোট রাখুন, এটাই টানেলের নাম হবে।

৩. **চালু করা (GUI):** WireGuard খুলে **Import tunnel(s) from file** → `.conf` বাছুন → **Activate**। ব্রাউজারে https://ifconfig.me খুললে VPN সার্ভারের IP দেখাবে।

৪. **রিবুটের পর নিজে চালু রাখতে (সার্ভিস হিসেবে):** PowerShell/CMD **Administrator** হিসেবে খুলে:
```
& "C:\Program Files\WireGuard\wireguard.exe" /installtunnelservice "C:\path\to\tz1.conf"
```
এটি লগইন ছাড়াই বুটের সময় চালু হয়। বন্ধ করে সরাতে:
```
& "C:\Program Files\WireGuard\wireguard.exe" /uninstalltunnelservice tz1
```

> ### ⚠️ RDP দিয়ে ঢুকে থাকলে সাবধান
> কনফিগে `AllowedIPs = 0.0.0.0/0, ::/0` থাকায় সার্ভারের **সব** ট্রাফিক VPN-এ চলে যায় (সঙ্গে Windows-এর kill-switch ব্লকও বসে)। এতে আপনার RDP সংযোগ কেটে যেতে এবং আপনি সার্ভারের বাইরে আটকে যেতে পারেন।
>
> **নিরাপদ উপায়:**
> 1. আগে প্রোভাইডারের **Web/VNC কনসোল** খুলে রাখুন, আটকে গেলে ওখান থেকে ঢুকে টানেল বন্ধ করা যাবে।
> 2. কনফিগের `AllowedIPs` লাইনে নিজের RDP করা পিসির পাবলিক IP বাদ দিন। এর কমান্ড (যেকোনো কম্পিউটারে Python থাকলে; `203.0.113.5` এর জায়গায় নিজের পাবলিক IP):
> ```
> python3 -c "import ipaddress as i;n=i.ip_network('0.0.0.0/0');print(', '.join(map(str,sorted(n.address_exclude(i.ip_network('203.0.113.5/32'))))))"
> ```
> যে লম্বা তালিকা আসবে সেটা `AllowedIPs = ` এর পর বসান (`::/0` মুছে দিন)। আপনার IP বদলালে আবার ঢোকা কঠিন হবে, তাই কনসোলের সুবিধা রাখুন।
> 3. শুধু সার্ভারের ভেতর থেকে VPN-এ ব্রাউজ করতে চাইলে বা সরাসরি কনসোলে বসে থাকলে এই সমস্যা নেই।

### macOS / Linux
WireGuard অ্যাপ (macOS) অথবা `sudo apt install wireguard` (Linux) দিয়ে `.conf` ইমপোর্ট করুন। Linux-এ `sudo wg-quick up ./tz-নাম.conf`।

---

## পাসওয়ার্ড বদলানো (গুরুত্বপূর্ণ)
```
cd ~/WireGuard
nano .env          # ADMIN_PASSWORD= লাইনে নতুন পাসওয়ার্ড দিন, সেভ করুন
docker compose up -d
```
কমপক্ষে ৮ অক্ষর। ডিফল্ট পাসওয়ার্ড (`tzalmamun`) চললে প্যানেলে লাল সতর্কতা দেখায়।

## কনফিগ (`.env`)
| নাম | ডিফল্ট | কাজ |
|---|---|---|
| `ADMIN_PASSWORD` | `tzalmamun` | অ্যাডমিন পাসওয়ার্ড |
| `WG_PORT` | `51820` | WireGuard UDP পোর্ট |
| `PANEL_PORT` | `4444` | প্যানেলের TCP পোর্ট |
| `SERVER_HOST` | নিজে শনাক্ত | কনফিগে যে IP/ডোমেইন বসবে |
| `PANEL_BIND` | `0.0.0.0` | `127.0.0.1` দিলে প্যানেল ইন্টারনেট থেকে লুকানো (SSH টানেল দিয়ে ঢুকতে হয়) |
| `WG_DNS` | `1.1.1.1, 8.8.8.8` | ক্লায়েন্টের DNS |
| `WG_MTU` | `1380` | MTU |
| `TZ_OFFSET_HOURS` | `6` | প্যানেলের সময় ও মেয়াদের হিসাব (UTC + এই সংখ্যা) |

বদলানোর পর: `cd ~/WireGuard && docker compose up -d`। পোর্ট বা `SERVER_HOST` বদলালে আগের ইউজারদের কনফিগ আবার ডাউনলোড করে অ্যাপে দিতে হবে (এন্ডপয়েন্ট বদলায়)।

## প্রতিদিনের কমান্ড
```
cd ~/WireGuard
docker compose ps           # চলছে কি না
docker compose logs -f      # লগ (বের হতে Ctrl+C)
docker compose restart      # রিস্টার্ট
docker compose down         # বন্ধ
```

## আপডেট
```
cd ~/WireGuard
git pull
docker compose up -d --build
```
ইউজার ও ব্যবহারের হিসাব `data/` ফোল্ডারে থাকে, তাই অক্ষত থাকে।

## ব্যাকআপ ও নতুন VPS-এ ইউজার সরানো
সব ইউজার, কী ও ব্যবহারের হিসাব `~/WireGuard/data/state.json` ফাইলে। এটি কপি করে রাখুন (যেমন `scp root@VPS_IP:~/WireGuard/data/state.json .`)। নতুন VPS-এ ধাপ ৪ করে `docker compose up` এর **আগে** `data/` ফোল্ডার বানিয়ে ফাইলটি `~/WireGuard/data/state.json` নামে বসালে সব ইউজার ফিরে আসে।
- নতুন VPS-এর IP আলাদা হলে ইউজারদের **নতুন কনফিগ ডাউনলোড করে** অ্যাপে দিতে হবে।
- এই ফাইলে প্রাইভেট কী আছে, কারও সাথে শেয়ার করবেন না এবং GitHub-এ তুলবেন না (`.gitignore`-এ বাদ দেওয়া আছে)।

## মুছে ফেলা
```
cd ~/WireGuard && docker compose down && cd ~ && rm -rf ~/WireGuard
```

## সমস্যা হলে
| সমস্যা | সমাধান |
|---|---|
| `address already in use` পোর্ট এরর | `.env`-এ `WG_PORT` বা `PANEL_PORT` বদলে `docker compose up -d`। কে ব্যবহার করছে: `ss -ulpn \| grep 51820` |
| প্যানেল খুলছে না | প্রোভাইডারের ফায়ারওয়াল ও ufw-তে TCP 4444 খুলুন (ধাপ ৩); `docker compose ps` ও `logs` দেখুন |
| কানেক্ট হয় না | **UDP** 51820 খোলা কি না দেখুন; ক্লায়েন্টে ইউজার `disabled`/`expired`/`limit reached` কি না দেখুন |
| কানেক্ট হয় কিন্তু ইন্টারনেট নেই | `docker compose logs`-এ এরর দেখুন; VPS-এ `modprobe wireguard` চালিয়ে দেখুন; VPS KVM কি না যাচাই করুন |
| `iptables`/বিল্ড এরর | লগের পুরো এরর কপি করে ইস্যু খুলুন |
| পাসওয়ার্ড ভুলে গেছেন | `grep ADMIN_PASSWORD ~/WireGuard/.env` |
| বারবার ভুল পাসওয়ার্ডে ব্লক | একই IP থেকে ১০ মিনিটে ৬ বার ভুল হলে ১৫ মিনিট ব্লক, অপেক্ষা করুন |
| ইউজার নিজে বন্ধ হয়ে গেছে | তালিকায় `limit reached` বা `expired` দেখুন। লিমিট/মেয়াদ বাড়ালে বা Reset করলে চালু হবে |

## নিরাপত্তা নোট
- ডিফল্ট পাসওয়ার্ড অবশ্যই বদলান।
- প্যানেলে HTTPS আছে, তবে সার্টিফিকেট সেলফ-সাইনড। নিজের ডোমেইন ও রিভার্স প্রক্সি দিতে চাইলে `PANEL_BIND=127.0.0.1` দিন।
- লগইনে ব্রুট-ফোর্স ব্লক, সেশন কুকি `HttpOnly`/`SameSite=Strict`/`Secure`, ফর্মে CSRF সুরক্ষা আছে।
- প্যানেলের পোর্ট শুধু নিজের IP-র জন্য খোলা রাখলে সবচেয়ে নিরাপদ (প্রোভাইডারের ফায়ারওয়াল দিয়ে)।

## সীমাবদ্ধতা
- শুধু IPv4 ট্রাফিক রাউট হয় (ক্লায়েন্টের IPv6 টানেলের ভেতরে ফেলে দেওয়া হয়, যাতে IPv6 লিক না হয়)।
- একটি সার্ভার, একজন অ্যাডমিন।
- ক্লায়েন্ট পুল `10.8.0.0/20` (প্রায় ৪০০০ ইউজার)।
- ডাটা হিসাব সার্ভারের গণনা অনুযায়ী (WireGuard কাউন্টার), প্রতি ~২০ সেকেন্ডে আপডেট হয়।

## ফাইল তালিকা
| ফাইল | কাজ |
|---|---|
| `app.py` | প্যানেল + WireGuard ম্যানেজার |
| `Dockerfile`, `docker-compose.yml` | Docker সেটআপ |
| `.env.example` | কনফিগের নমুনা |
| `build.py` | ঐচ্ছিক। `python3 build.py` চালালে পুরনো ধরনের একক-ফাইল ইনস্টলার `tz-wg-install.sh` বানায় (সাধারণ ব্যবহারে লাগে না, `git clone` পদ্ধতিই যথেষ্ট) |

## GitHub-এ আপলোড
নিজের কম্পিউটারে ফোল্ডারে গিয়ে (আগে github.com-এ `WireGuard` নামে খালি রিপোজিটরি বানিয়ে নিন):
```
cd TZ-WG
git init
git add .
git commit -m "TZ WireGuard"
git branch -M main
git remote add origin https://github.com/tzalmamun/WireGuard.git
git push -u origin main
```
পরে কোড বদলালে: `git add . && git commit -m "update" && git push`। প্রাইভেট রিপোজিটরি হলে VPS-এ ক্লোনের সময় GitHub ইউজারনেম ও Personal Access Token লাগবে। লাইসেন্স আপনার ইচ্ছামতো যোগ করুন (এখানে কোনোটি দেওয়া নেই)।
