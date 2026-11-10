# CardioIA — Fase 7 | README técnico de implantação

> **Objetivo:** referência rápida para o integrante 4 consolidar a documentação da Fase 7. Registra a implantação e os testes realizados em **09/11/2026**. Projeto acadêmico com dados simulados, sem finalidade de diagnóstico clínico.

## 1. Arquitetura

```text
ESP32 (Wokwi / MicroPython)
       | HTTP, leituras a cada ~5 s
       v
Backend FastAPI (Render)
       | GET /health e GET /api/leituras?limite=20
       +--------------------------+
       v                          v
Frontend Vite (Vercel)     Mobile Expo (APK Android / EAS)
```

- **GitHub oficial:** https://github.com/JV-004/CardioIA-Fase7
- **Aplicação Web:** https://cardio-ia-fase7-delta.vercel.app
- **Backend:** https://cardioia-backend-djsj.onrender.com
- **Health check:** https://cardioia-backend-djsj.onrender.com/health
- **Pull Request integrado:** https://github.com/JV-004/CardioIA-Fase7/pull/4

## 2. Entrega realizada nesta etapa

**Contribuição versionada e incorporada à `main` do repositório oficial pelo PR #4:**

| Arquivo | Alteração |
|---|---|
| `Frontend/vercel.json` | Reescrita das rotas SPA para `/index.html` na Vercel |
| `Mobile/src/services/api.ts` | URL da API via `EXPO_PUBLIC_API_URL`, com fallback para o Render |

Além do código incorporado, foram **executados e validados**: publicação Web, build de APK Android pelo EAS, execução em emulador Android Studio e fluxo de leituras Wokwi → Render → Web/Mobile.

**Divisão de responsabilidades:** a hospedagem/configuração original do backend Render é da frente de backend (João); esta contribuição conectou e testou os clientes Web/Mobile com a API existente. O integrante 4 consolida as evidências e a documentação.

## 3. Ferramentas e links

| Ferramenta | Link | Uso |
|---|---|---|
| GitHub | https://github.com/JV-004/CardioIA-Fase7 | Código e histórico |
| Vercel | https://vercel.com/ | Deploy Web |
| Render | https://dashboard.render.com/ | Painel do backend (acesso do responsável) |
| Wokwi | https://wokwi.com/ | ESP32 simulado |
| Expo EAS | https://expo.dev/ | Compilação Android |
| Build Android validado | https://expo.dev/accounts/taynaesteves-team/projects/cardioia/builds/03a7c9f0-903d-4607-918c-50ff9d60d865 | Evidência do build |
| APK validado | https://expo.dev/artifacts/eas/7tdOKuCQB1dAh2fsRM4aLjKU9222JSKtFk8syvfqzsg.apk | Instalador Android (disponibilidade temporária) |

## 4. Como reproduzir o funcionamento

### 4.1 Backend (Render — responsável: João)

1. Confirmar que `https://cardioia-backend-djsj.onrender.com/health` responde.
2. Se a API estiver adormecida no plano gratuito, aguardar aproximadamente 60 s na primeira chamada.
3. Para problemas de backend, consultar logs, variáveis de ambiente e comandos de deploy **na conta do responsável**. Não recriar o serviço sem necessidade.

> Os comandos de build/start, segredos e configuração interna do Render não foram levantados nesta contribuição.

### 4.2 Frontend Web (Vercel)

1. Importar o repositório para a Vercel, usando **Root Directory: `Frontend`**.
2. Confirmar o build Vite (`npm run build`, saída usual `dist`, conforme `Frontend/package.json`).
3. Definir a variável de ambiente em **Production** e **Preview**:

```env
VITE_API_URL=https://cardioia-backend-djsj.onrender.com
```

4. Fazer deploy e abrir https://cardio-ia-fase7-delta.vercel.app.
5. Verificar `Sistema online`, leituras e protocolos no dashboard.

Arquivo `Frontend/vercel.json`:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

**Nota:** alterações em `VITE_API_URL` exigem novo build. Confirmar no painel Vercel qual repositório/branch está conectado; o merge no GitHub não comprova redeploy automático.

### 4.3 Aplicativo Android (Expo / EAS)

Pré-requisitos: Node.js/npm, projeto `Mobile`, conta Expo com acesso, Android Studio e emulador (ou dispositivo Android compatível).

```powershell
cd Mobile
npm install
npx eas build --platform android --profile preview
```

- Perfil testado: `preview` / distribuição interna / APK Android / Expo SDK 58.
- Build bem-sucedido em 09/11/2026, ID `03a7c9f0-903d-4607-918c-50ff9d60d865`.
- APK instalado e executado no emulador Android Studio `Medium_Phone_API_37.0`.
- O arquivo `Mobile/src/services/api.ts` usa:

```ts
const API_URL =
  process.env.EXPO_PUBLIC_API_URL || 'https://cardioia-backend-djsj.onrender.com'
```

Variável opcional de build:

```env
EXPO_PUBLIC_API_URL=https://cardioia-backend-djsj.onrender.com
```

**Importante:** se mudar a URL do backend, gerar **novo APK**. Antes de reconstruir, conferir `Mobile/eas.json`, `app.json` e as permissões do projeto Expo.

### 4.4 ESP32 simulado (Wokwi)

1. Abrir o projeto CardioIA no Wokwi (URL específica pendente de registro).
2. Conferir em `main.py`:

```python
BACKEND_URL = "https://cardioia-backend-djsj.onrender.com"
DEVICE_ID = "esp32-wokwi-01"
WIFI_SSID = "Wokwi-GUEST"
INTERVALO_LEITURA_MS = 5000
SIMULAR_OFFLINE_30S = False
BPM_ALEATORIO = False
```

3. Iniciar a simulação e conferir o console de conexão Wi-Fi e envio.
4. Ajustar os potenciômetros de **BPM** e **SpO₂**; verificar atualização no site e no APK (interface com atualização automática a cada ~5 s).

Sensores/componentes visíveis: ESP32, DHT22, dois potenciômetros, OLED e LEDs de status.

## 5. Testes e evidências

| Teste | Evidência / resultado |
|---|---|
| Web | Dashboard publicado, online, com leituras e protocolos |
| Android | EAS Build `Succeeded`; APK aberto no emulador |
| Integração | Leituras do Wokwi recebidas em Web e Mobile |
| Cenário A | **169 BPM, SpO₂ 94%, 36,5 °C** → risco exibido **18% (baixo)**, alerta de taquicardia e monitoramento intensivo |
| Cenário B | **129 BPM, SpO₂ 88%, 36,5 °C** → risco exibido **85% (alto)**, monitoramento intensivo e estado de emergência |
| GitHub | PR #4 marcado `Merged` em `JV-004:main` |

**Atenção à interpretação:** alertas locais e classificação preditiva são mecanismos distintos. O código `IoT/logica.py` registra limites locais, como BPM >120, temperatura >38 °C e SpO₂ <88%; isso **não** define sozinho o percentual de risco calculado pelo backend. Não foram comprovados, nesta etapa, todos os cenários intermediários nem a acurácia clínica do modelo.

**Prints úteis para o integrante 4:** Wokwi + console, Android com risco baixo/alto, dashboard Web com risco alto, build EAS `Succeeded`, PR #4 `Merged`. Print do serviço Render deve ser solicitado ao responsável pelo backend.

## 6. GitHub — como a contribuição foi incorporada

A cópia ZIP original não tinha `.git`. Foi criado um clone válido do fork e utilizada a branch `feat/fase7-deploy`:

```powershell
cd "$HOME\Downloads"
git clone --branch feat/fase7-deploy https://github.com/tayesteves/CardioIA-Fase7.git CardioIA-Deploy
cd "$HOME\Downloads\CardioIA-Deploy"

git add Frontend/vercel.json Mobile/src/services/api.ts
git commit -m "feat: configura deploy web e integracao mobile com backend"
git push origin feat/fase7-deploy
```

Depois foi aberto e mesclado o **PR #4** de `tayesteves:feat/fase7-deploy` para `JV-004:main`. Merge confirmado no repositório oficial.

## 7. Problemas encontrados

| Problema | Causa / solução |
|---|---|
| `fatal: not a git repository` | Comandos na pasta ZIP; usar clone Git válido |
| `Copy-Item` não encontra `api.ts` | O arquivo correto é `Mobile/src/services/api.ts`, não `Frontend/src/services/api.ts` |
| `Get-ChildItem -Recurse` falha | Busca atravessou `Mobile/node_modules`; limitar pesquisa às pastas `src` |
| Render demora a responder | Serviço gratuito pode suspender por inatividade; aguardar e testar `/health` |
| `MBEDTLS_ERR_SSL_CONN_EOF` intermitente no Wokwi | Verificar conexão, logs e tentar novo envio; integração funcionou nos testes subsequentes |

## 8. Pendências para o integrante 4 consolidar

- Obter com **João** print do Render e detalhes de deploy (branch, comandos, dependências, segredos **sem expor valores**).
- Registrar a **URL exata do projeto Wokwi**.
- Confirmar no painel Vercel o repositório/branch e as configurações finais de build.
- Conferir `eas.json`, versões de dependências e instruções de instalação na versão final do repositório.
- Organizar os prints por teste e incluir as URLs de evidência.
- Se o escopo exigir, documentar testes adicionais de risco médio, autenticação, persistência e recuperação de falhas.

---

**Resumo para a entrega:** publicação Web e APK Android concluídos; integração com backend e Wokwi demonstrada; alterações de configuração incorporadas ao repositório oficial via PR #4. Backend Render é responsabilidade da frente de backend; este README documenta sua utilização e integração, não sua implantação original.
