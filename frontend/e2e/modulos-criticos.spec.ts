import { expect, type Page, test } from "@playwright/test";

function jsonResponse(body: unknown) {
  return {
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(body),
  };
}

async function setupAdminMocks(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());

    if (req.method() === "GET" && url.pathname === "/api/v1/admin/usuarios") {
      await route.fulfill(
        jsonResponse({
          items: [
            {
              id: "user-1",
              email: "admin@hw1.local",
              nome: "Admin HW1",
              role: "admin",
            },
          ],
          total: 1,
          page: 1,
          per_page: 20,
        })
      );
      return;
    }

    if (req.method() === "GET" && url.pathname === "/api/v1/health/smoke") {
      await route.fulfill(
        jsonResponse({
          overall_status: "ok",
          checked_at: "2026-03-10T12:00:00Z",
          total_checks: 4,
          failed_checks: [],
          checks: {
            pcd: { status: "ok", classes: 3 },
            ttd: { status: "ok", regras: 4 },
            observabilidade: { status: "ok", incidents_open: 0 },
            backup: { status: "ok", snapshots: 2 },
          },
        })
      );
      return;
    }

    await route.fulfill({ status: 404, body: "Not mocked" });
  });
}

async function setupEntrevistasMocks(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());

    if (req.method() === "GET" && url.pathname === "/api/v1/roteiros") {
      await route.fulfill(
        jsonResponse({
          items: [
            {
              id: "roteiro-1",
              titulo: "Roteiro RH",
              area: "RH",
              versao: 1,
              status: "ativo",
              total_perguntas: 2,
            },
          ],
          total: 1,
          page: 1,
          per_page: 20,
        })
      );
      return;
    }

    if (req.method() === "GET" && url.pathname === "/api/v1/roteiros/roteiro-1") {
      await route.fulfill(
        jsonResponse({
          id: "roteiro-1",
          titulo: "Roteiro RH",
          descricao: "Fluxo RH",
          area: "RH",
          versao: 1,
          status: "ativo",
          perguntas: [
            {
              id: "q1",
              ordem: 1,
              texto: "Possui contrato?",
              tipo: "boolean",
              obrigatoria: true,
              secao: null,
              metadado_alvo: null,
              opcoes: null,
              condicoes: [],
            },
            {
              id: "q2",
              ordem: 2,
              texto: "Quantidade de anexos",
              tipo: "numero",
              obrigatoria: false,
              secao: null,
              metadado_alvo: null,
              opcoes: null,
              condicoes: [],
            },
          ],
        })
      );
      return;
    }

    if (
      req.method() === "POST" &&
      url.pathname === "/api/v1/roteiros/roteiro-1/simular"
    ) {
      await route.fulfill(
        jsonResponse({
          perguntas: [
            {
              id: "q1",
              ordem: 1,
              texto: "Possui contrato?",
              tipo: "boolean",
              secao: null,
              visivel: true,
              obrigatoria: true,
            },
            {
              id: "q2",
              ordem: 2,
              texto: "Quantidade de anexos",
              tipo: "numero",
              secao: null,
              visivel: true,
              obrigatoria: false,
            },
          ],
          pendencias: [],
          pode_concluir: true,
        })
      );
      return;
    }

    await route.fulfill({ status: 404, body: "Not mocked" });
  });
}

async function setupPcdMocks(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());

    if (req.method() === "GET" && url.pathname === "/api/v1/pcd/arvore") {
      await route.fulfill(
        jsonResponse([
          {
            id: "classe-1",
            pai_id: null,
            tipo: "classe",
            codigo: "001",
            titulo: "Classe RH",
            descricao: "Classe raiz",
            codigo_conarq: "1.1",
            versao: 2,
            status: "ativo",
            nivel_sigilo: "publico",
            metadados: {},
            filhos: [],
          },
        ])
      );
      return;
    }

    if (req.method() === "GET" && url.pathname === "/api/v1/pcd/classe-1/versoes") {
      await route.fulfill(
        jsonResponse([
          {
            id: "v1",
            pcd_nivel_id: "classe-1",
            versao: 1,
            dados_snapshot: {
              tipo: "classe",
              codigo: "001",
              titulo: "Classe RH antiga",
              descricao: "Antiga",
              codigo_conarq: "1.0",
              metadados: { setor: "RH" },
            },
            justificativa: "Inicial",
            status: "aprovado",
            created_at: "2026-03-01T09:00:00Z",
          },
          {
            id: "v2",
            pcd_nivel_id: "classe-1",
            versao: 2,
            dados_snapshot: {
              tipo: "classe",
              codigo: "001",
              titulo: "Classe RH",
              descricao: "Atual",
              codigo_conarq: "1.1",
              metadados: { setor: "RH", responsavel: "Arquivo" },
            },
            justificativa: "Ajuste",
            status: "pendente",
            created_at: "2026-03-05T10:00:00Z",
          },
        ])
      );
      return;
    }

    if (
      req.method() === "GET" &&
      url.pathname === "/api/v1/pcd/classe-1/controle-seguranca"
    ) {
      await route.fulfill(
        jsonResponse({
          pcd_nivel_id: "classe-1",
          metadados_obrigatorios: ["setor"],
          permissoes_por_papel: { arquivista: ["ler", "editar"] },
          unidades_autorizadas: ["SP"],
        })
      );
      return;
    }

    if (
      req.method() === "POST" &&
      url.pathname === "/api/v1/pcd/classe-1/validar-metadados"
    ) {
      await route.fulfill(
        jsonResponse({
          pcd_nivel_id: "classe-1",
          valido: true,
          faltantes: [],
        })
      );
      return;
    }

    await route.fulfill({ status: 404, body: "Not mocked" });
  });
}

async function setupTtdMocks(page: Page) {
  const holds = [
    {
      id: "hold-1",
      pcd_nivel_id: "classe-1",
      motivo: "Auditoria anual",
      tipo: "auditoria",
      status: "ativo",
      data_inicio: "2026-03-01T10:00:00Z",
    },
  ];

  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const url = new URL(req.url());

    if (req.method() === "GET" && url.pathname === "/api/v1/pcd/arvore") {
      await route.fulfill(
        jsonResponse([
          {
            id: "classe-1",
            tipo: "classe",
            codigo: "001",
            titulo: "Classe RH",
            filhos: [],
          },
        ])
      );
      return;
    }

    if (req.method() === "GET" && url.pathname === "/api/v1/ttd/regras") {
      await route.fulfill(jsonResponse([]));
      return;
    }

    if (req.method() === "GET" && url.pathname === "/api/v1/ttd/holds") {
      await route.fulfill(jsonResponse(holds));
      return;
    }

    if (req.method() === "GET" && url.pathname === "/api/v1/ttd/ordens") {
      await route.fulfill(jsonResponse([]));
      return;
    }

    if (req.method() === "PATCH" && url.pathname === "/api/v1/ttd/holds/hold-1/revogar") {
      holds[0] = { ...holds[0], status: "revogado" };
      await route.fulfill(jsonResponse(holds[0]));
      return;
    }

    await route.fulfill({ status: 404, body: "Not mocked" });
  });
}

test("admin executa smoke check operacional", async ({ page }) => {
  await setupAdminMocks(page);

  await page.goto("/dashboard/admin");
  await page.getByRole("button", { name: "Executar smoke check" }).click();

  await expect(page.getByText("Smoke check operacional concluído sem falhas.")).toBeVisible();
  await expect(page.getByText("Status geral: ok · Checks: 4")).toBeVisible();
  await expect(page.getByText("pcd · ok")).toBeVisible();
});

test("entrevistas executa dry-run condicional", async ({ page }) => {
  await setupEntrevistasMocks(page);

  await page.goto("/dashboard/entrevistas");
  await page.getByRole("button", { name: "Roteiro RH" }).click();
  await page.getByRole("button", { name: "Executar dry-run" }).click();

  await expect(page.getByText("Pode concluir: Sim")).toBeVisible();
  await expect(page.getByText("#1 · Visível · Obrigatória")).toBeVisible();
});

test("pcd valida metadados obrigatórios de classe", async ({ page }) => {
  await setupPcdMocks(page);

  await page.goto("/dashboard/pcd");
  await page.getByRole("button", { name: "[classe] 001 · Classe RH" }).click();
  await page
    .getByPlaceholder('Metadados do documento em JSON (ex.: {"setor":"RH"})')
    .fill('{"setor":"RH"}');
  await page.getByRole("button", { name: "Validar metadados" }).click();

  await expect(page.getByText("Resultado: Válido")).toBeVisible();
  await expect(page.getByText("Faltantes: nenhum")).toBeVisible();
});

test("ttd revoga legal hold ativo", async ({ page }) => {
  await setupTtdMocks(page);

  await page.goto("/dashboard/ttd");
  await expect(page.getByText("Status: ativo")).toBeVisible();

  await page.getByRole("button", { name: "Revogar" }).click();

  await expect(page.getByText("Status: revogado")).toBeVisible();
});
