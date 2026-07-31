import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import vm from "node:vm";

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadApi() {
  const source = readFileSync(resolve(__dirname, "..", "..", "web", "library-trash.js"), "utf8");
  const moduleObj = { exports: {} };
  const sandbox = { module: moduleObj, exports: moduleObj.exports, window: {}, console };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { filename: "web/library-trash.js" });
  return moduleObj.exports;
}

test("selection and cancel never call the transport", async () => {
  const transports = [];
  const states = [];
  const controller = loadApi().createController({
    listTrash: async () => {
      transports.push("listTrash");
      return { library: "C:\\Books", trash: [] };
    },
    trashBook: async () => transports.push("trashBook"),
    restoreBook: async () => transports.push("restoreBook"),
    onChange: (state) => states.push(state),
    onMutation: async () => {},
  });
  controller.select({ directory: "demo", title: "Demo" });
  controller.requestTrash();
  assert.equal(controller.snapshot().pending.directory, "demo");
  controller.cancelTrash();
  assert.equal(controller.snapshot().pending, null);
  assert.deepEqual(transports, []);
  assert.equal(states.at(-1).busy, false);
});

test("confirmed recycle is busy, forwards result, refreshes, and clears selection", async () => {
  let release;
  const mutations = [];
  const events = [];
  const controller = loadApi().createController({
    listTrash: async () => {
      events.push("refresh");
      return { library: "C:\\Books", trash: [{ trash_id: "t1", valid: true }] };
    },
    trashBook: () => new Promise((resolve) => { release = resolve; }),
    restoreBook: async () => {},
    onChange: () => {},
    onMutation: async (result, kind) => {
      events.push("mutation");
      mutations.push({ result, kind });
    },
  });
  controller.select({ directory: "demo", title: "Demo" });
  controller.requestTrash();
  const pending = controller.confirmTrash();
  assert.equal(controller.snapshot().busy, true);
  await Promise.resolve();
  release({ status: "trashed", trash_id: "t1", was_active: true });
  const result = await pending;
  assert.equal(result.trash_id, "t1");
  assert.equal(controller.snapshot().busy, false);
  assert.equal(controller.snapshot().selected, null);
  assert.equal(controller.snapshot().trash.length, 1);
  assert.equal(mutations[0].kind, "trash");
  assert.equal(mutations[0].result.was_active, true);
  assert.deepEqual(events, ["mutation", "refresh"]);
});

test("restore errors remain visible and always clear busy", async () => {
  const controller = loadApi().createController({
    listTrash: async () => ({ library: "C:\\Books", trash: [] }),
    trashBook: async () => {},
    restoreBook: async () => { throw new Error("restore failed"); },
    onChange: () => {},
    onMutation: async () => {},
  });
  await assert.rejects(controller.restore("t1"), /restore failed/);
  assert.equal(controller.snapshot().busy, false);
  assert.equal(controller.snapshot().error, "restore failed");
});

test("snapshots cannot mutate selected, pending, or trash state", async () => {
  const directories = [];
  const controller = loadApi().createController({
    listTrash: async () => ({
      library: "C:\\Books",
      trash: [{ trash_id: "t1", valid: false }],
    }),
    trashBook: async (directory) => {
      directories.push(directory);
      return { status: "trashed" };
    },
    restoreBook: async () => {},
    onChange: () => {},
    onMutation: async () => {},
  });
  await controller.refresh();
  controller.select({ directory: "demo", title: "Demo" });
  controller.requestTrash();

  const snapshot = controller.snapshot();
  snapshot.selected.directory = "changed-selection";
  snapshot.pending.directory = "changed-pending";
  snapshot.trash[0].trash_id = "changed-trash";
  snapshot.trash[0].valid = true;

  const isolated = controller.snapshot();
  assert.equal(isolated.selected.directory, "demo");
  assert.equal(isolated.pending.directory, "demo");
  assert.equal(isolated.trash[0].trash_id, "t1");
  assert.equal(isolated.trash[0].valid, false);
  await controller.confirmTrash();
  assert.deepEqual(directories, ["demo"]);
});

test("synchronous transport errors remain visible and always clear busy", async () => {
  const controller = loadApi().createController({
    listTrash: async () => ({ library: "C:\\Books", trash: [] }),
    trashBook: async () => {},
    restoreBook: () => { throw new Error("synchronous restore failed"); },
    onChange: () => {},
    onMutation: async () => {},
  });
  await assert.rejects(controller.restore("t1"), /synchronous restore failed/);
  assert.equal(controller.snapshot().busy, false);
  assert.equal(controller.snapshot().error, "synchronous restore failed");
});

test("a second mutation is rejected while recycle is running", async () => {
  let release;
  const controller = loadApi().createController({
    listTrash: async () => ({ library: "C:\\Books", trash: [] }),
    trashBook: () => new Promise((resolve) => { release = resolve; }),
    restoreBook: async () => ({ status: "restored" }),
    onChange: () => {},
    onMutation: async () => {},
  });
  controller.select({ directory: "demo", title: "Demo" });
  controller.requestTrash();
  const first = controller.confirmTrash();
  await assert.rejects(controller.restore("t1"), /already running/);
  release({ status: "trashed", trash_id: "t1" });
  await first;
});

test("refresh preserves invalid items for unavailable UI rendering", async () => {
  let restoreCalls = 0;
  const controller = loadApi().createController({
    listTrash: async () => ({
      library: "C:\\Books",
      trash: [{ trash_id: "bad", valid: false, error: "trash tag missing" }],
    }),
    trashBook: async () => {},
    restoreBook: async () => { restoreCalls += 1; },
    onChange: () => {},
    onMutation: async () => {},
  });
  await controller.refresh();
  assert.equal(controller.snapshot().trash[0].valid, false);
  assert.equal(controller.snapshot().trash[0].error, "trash tag missing");
  assert.equal(restoreCalls, 0);
});
