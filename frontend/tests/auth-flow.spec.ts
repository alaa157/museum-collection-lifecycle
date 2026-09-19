import { test, expect } from "@playwright/test";

const ADMIN_EMAIL =
  process.env.E2E_ADMIN_EMAIL ??
  "admin@gmail.com";

const ADMIN_PASSWORD =
  process.env.E2E_ADMIN_PASSWORD ??
  "ChangeThisPassword123!";

test.describe(
  "Museum Collection Lifecycle Platform",
  () => {
    test("1. Login", async ({ page }) => {
      await page.goto("/login");

      await page
        .getByLabel("Email")
        .fill(ADMIN_EMAIL);

      await page
        .getByLabel("Password")
        .fill(ADMIN_PASSWORD);

      await page
        .getByRole("button", {
          name: /sign in/i
        })
        .click();

      await expect(
        page.getByRole("heading", {
          name: "Collection workspace"
        })
      ).toBeVisible();
    });

    test("2. Create collection item page", async ({
      page
    }) => {
      await login(page);

      await page.goto("/collection/new");

      await expect(
        page.getByRole("heading", {
          name: "Register collection item"
        })
      ).toBeVisible();

      await page
        .getByLabel("Accession number")
        .fill(
          `E2E-${Date.now()}`
        );

      await page
        .getByLabel("Object number")
        .fill(
          `E2E-OBJ-${Date.now()}`
        );

      await page
        .getByLabel("Title")
        .fill(
          "E2E Conservation Record"
        );
    });

    test("3. Search collection", async ({
      page
    }) => {
      await login(page);

      await page.goto("/collection");

      const search =
        page.getByPlaceholder(
          "Accession, object number, title"
        );

      await search.fill(
        "Evening Along the Canal"
      );

      await page
        .getByRole("button", {
          name: "Search",
          exact: true
        })
        .click();

      await expect(
        page.getByText(
          "Evening Along the Canal"
        )
      ).toBeVisible();
    });

    test("4. Open collection item", async ({
      page
    }) => {
      await login(page);

      await page.goto("/collection");

      await page
        .getByText(
          "Evening Along the Canal"
        )
        .click();

      await expect(
        page.getByRole("heading", {
          name: "Evening Along the Canal"
        })
      ).toBeVisible();
    });

    test("5. Movements page", async ({
      page
    }) => {
      await login(page);

      await page.goto("/movements");

      await expect(
        page.getByRole("heading", {
          name: "Movement requests"
        })
      ).toBeVisible();
    });

    test("6. Approve movement UI", async ({
      page
    }) => {
      await login(page);

      await page.goto("/movements");

      const approve =
        page.getByRole("button", {
          name: "Approve"
        });

      if (await approve.count()) {
        await expect(approve.first()).toBeVisible();
      }
    });

    test("7. Conservation page", async ({
      page
    }) => {
      await login(page);

      await page.goto(
        "/conservation"
      );

      await expect(
        page.getByRole("heading", {
          name: "Conservation"
        })
      ).toBeVisible();
    });

    test("8. Loans page", async ({
      page
    }) => {
      await login(page);

      await page.goto("/loans");

      await expect(
        page.getByRole("heading", {
          name: "Loans"
        })
      ).toBeVisible();
    });

    test("9. Notifications page", async ({
      page
    }) => {
      await login(page);

      await page.goto(
        "/notifications"
      );

      await expect(
        page.getByRole("heading", {
          name: "Notifications"
        })
      ).toBeVisible();
    });

    test("10. Audit page", async ({
      page
    }) => {
      await login(page);

      await page.goto("/audit");

      await expect(
        page.getByRole("heading", {
          name: "Audit history"
        })
      ).toBeVisible();
    });

    test("dashboard charts render", async ({
      page
    }) => {
      await login(page);

      await page.goto("/dashboard");

      await expect(
        page.getByText(
          "Collection by status"
        )
      ).toBeVisible();

      await expect(
        page.getByText(
          "Collection by object type"
        )
      ).toBeVisible();
    });

    test("users and roles page", async ({
      page
    }) => {
      await login(page);

      await page.goto("/users");

      await expect(
        page.getByRole("heading", {
          name: "Users & roles"
        })
      ).toBeVisible();

      await expect(
        page.getByText("ADMIN")
      ).toBeVisible();
    });
  }
);

async function login(page: any) {
  await page.goto("/login");

  await page
    .getByLabel("Email")
    .fill(ADMIN_EMAIL);

  await page
    .getByLabel("Password")
    .fill(ADMIN_PASSWORD);

  await page
    .getByRole("button", {
      name: /sign in/i
    })
    .click();

  await page.waitForURL(
    "**/dashboard"
  );
}
