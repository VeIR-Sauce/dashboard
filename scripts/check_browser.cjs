#!/usr/bin/env node
/* An installed Chromium and Node 18+ are enough; no browser package or server. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const {pathToFileURL} = require("node:url");
const {spawn} = require("node:child_process");

async function main() {
  const site = path.resolve(process.argv[2] || "site-output");
  const screenshots = process.argv[3] && path.resolve(process.argv[3]);
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "veir-browser-"));
  const browser = spawn(process.env.CHROMIUM || "chromium", [
    "--headless", "--remote-debugging-pipe", "--disable-gpu", "--disable-dev-shm-usage",
    "--no-first-run", "--no-default-browser-check", "--disable-background-networking",
    "--disable-component-update", "--disable-extensions", "--disable-sync",
    "--disable-breakpad", "--disable-application-cache", "--disk-cache-size=1048576",
    "--media-cache-size=1048576", "--disable-gpu-shader-disk-cache",
    "--disable-features=MediaRouter,OptimizationHints,Translate",
    "--incognito", "--user-data-dir=" + profile, "about:blank"
  ], {stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"]});
  const pending = new Map(), errors = [];
  let sequence = 0, buffered = Buffer.alloc(0), stderr = "", session, transportError, closing = false;
  const closed = new Promise(resolve => browser.once("close", resolve));
  browser.stderr.on("data", chunk => { stderr = (stderr + chunk.toString()).slice(-16384); });
  browser.on("error", error => errors.push(error.message));
  function transportFailed(error) {
    transportError = error;
    if (!closing) errors.push("DevTools transport: " + error.message);
    for (const job of pending.values()) { clearTimeout(job.timer); job.reject(error); }
    pending.clear();
  }
  // Native Chrome may reset these pipes during shutdown. Handle the reset so
  // cleanup cannot replace an assertion failure with an unhandled Socket error.
  browser.stdio[3].on("error", transportFailed);
  browser.stdio[4].on("error", transportFailed);
  browser.once("close", () => transportFailed(new Error("Chromium closed its DevTools connection")));
  browser.stdio[4].on("data", chunk => {
    buffered = Buffer.concat([buffered, chunk]);
    let end;
    while ((end = buffered.indexOf(0)) !== -1) {
      const message = JSON.parse(buffered.subarray(0, end).toString());
      buffered = buffered.subarray(end + 1);
      if (message.id && pending.has(message.id)) {
        const job = pending.get(message.id); pending.delete(message.id); clearTimeout(job.timer);
        if (message.error) job.reject(new Error(JSON.stringify(message.error))); else job.resolve(message.result);
      } else if (message.method === "Runtime.exceptionThrown") {
        errors.push(JSON.stringify(message.params.exceptionDetails));
      }
    }
  });
  function send(method, params = {}, target = session) {
    if (transportError) return Promise.reject(transportError);
    return new Promise((resolve, reject) => {
      const id = ++sequence;
      const timer = setTimeout(() => { pending.delete(id); reject(new Error("CDP timed out: " + method)); }, 15000);
      pending.set(id, {resolve, reject, timer});
      browser.stdio[3].write(JSON.stringify({id, method, params, ...(target ? {sessionId: target} : {})}) + "\0");
    });
  }
  async function evaluate(expression) {
    const response = await send("Runtime.evaluate", {expression, returnByValue: true, awaitPromise: true});
    if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
    return response.result.value;
  }
  async function choose(id, value) {
    return evaluate("(() => {const element = document.getElementById(" + JSON.stringify(id) + "); element.value = " +
      JSON.stringify(value) + "; element.dispatchEvent(new Event(" +
      JSON.stringify(["scope", "cohort"].includes(id) ? "change" : "input") + ")); return element.value;})()");
  }
  const text = id => evaluate("document.getElementById(" + JSON.stringify(id) + ").textContent");
  async function until(expression) {
    for (let attempt = 0; attempt < 100; attempt++) {
      if (await evaluate(expression)) return;
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    throw new Error("Browser condition was not reached: " + expression);
  }
  async function screenshot(name) {
    if (!screenshots) return;
    const {data} = await send("Page.captureScreenshot", {format: "png", captureBeyondViewport: false});
    const bytes = Buffer.from(data, "base64");
    assert.ok(bytes.length < 1024 * 1024, "Viewport screenshot exceeded 1 MiB");
    fs.mkdirSync(screenshots, {recursive: true});
    fs.writeFileSync(path.join(screenshots, name + ".png"), bytes);
  }
  try {
    const target = await send("Target.createTarget", {url: "about:blank"}, null);
    session = (await send("Target.attachToTarget", {targetId: target.targetId, flatten: true}, null)).sessionId;
    await send("Page.enable"); await send("Runtime.enable");
    await send("Emulation.setDeviceMetricsOverride", {width: 1365, height: 960, deviceScaleFactor: 1, mobile: false});
    const navigation = await send("Page.navigate", {url: pathToFileURL(path.join(site, "index.html")).href});
    assert.ok(!navigation.errorText, "Page navigation failed: " + navigation.errorText);
    for (let attempt = 0; attempt < 100; attempt++) {
      if (await evaluate('document.getElementById("rows")?.children.length > 0')) break;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    assert.ok(await evaluate('document.getElementById("rows")?.children.length > 0'),
      "Page did not render: " + JSON.stringify(await evaluate('({url: location.href, text: document.body?.innerText.slice(0, 500)})')));
    const data = await evaluate('JSON.parse(document.getElementById("data").textContent)');
    const cohort = await evaluate('document.getElementById("cohort").value');
    const complete = data.reports.filter(r => r.cohort === cohort && r.complete).at(-1);
    if (complete) {
      assert.equal(await text("remaining"), String(complete.counts_by_scope.all.conformance_remaining));
      assert.equal(await text("passing"), String(complete.summary.test_counts.PASS));
      assert.equal(await evaluate('document.querySelectorAll(".chart svg").length'), 2);
    }
    await screenshot("desktop");
    await evaluate('document.querySelector("a[data-view=llvm-parse]").click()');
    await until('!document.getElementById("parsing-page").hidden');
    assert.equal(await evaluate('document.querySelectorAll("#parsing-operations tr").length'), data.catalog.operations.length);
    assert.match(await text("parsing-note"), /successful recorded example/);
    assert.equal(await evaluate('getComputedStyle(document.querySelector(".action-panel")).display'), "none");
    await choose("parse-status", "observed"); await choose("parse-search", "llvm.add");
    assert.ok(await evaluate('document.querySelectorAll("#parsing-operations tr").length > 0'));
    await send("Page.reload");
    await until('document.getElementById("parse-search")?.value === "llvm.add"');
    assert.equal(await evaluate('document.getElementById("parse-status").value'), "observed");
    await screenshot("parsing");
    await evaluate('document.querySelector("nav a[href=\\"#catalog\\"]").click()');
    await until('document.getElementById("catalog-details").open && !document.body.classList.contains("parsing-view")');
    await evaluate('history.back()');
    await until('document.body.classList.contains("parsing-view") && document.getElementById("parse-search").value === "llvm.add"');
    await evaluate('document.querySelector("#parsing-operations details").open = true');
    await evaluate('document.querySelector("#parsing-operations td:last-child a").click()');
    await until('document.getElementById("requirement-details").open && document.querySelector("#rows details")?.open');
    assert.equal(await evaluate('document.body.classList.contains("parsing-view")'), false);
    await evaluate('document.querySelector("a[data-view=overview]").click()');
    await until('location.hash === "#overview"');
    assert.equal(await evaluate('document.getElementById("catalog-details").open'), false);
    assert.ok(await evaluate('document.querySelectorAll("#actions article").length > 0'));
    await evaluate('document.querySelector("a[data-view=llvm]").click()');
    await until('document.getElementById("scope").value === "llvm-compat"');
    assert.match(await text("view-title"), /LLVM dialect compatibility/);
    await choose("stage", "verification"); await choose("status", "failed");
    await choose("search", "vector");
    const filterLink = await evaluate('location.href');
    await send("Page.reload");
    await until('document.getElementById("search")?.value === "vector"');
    assert.equal(await evaluate('location.href'), filterLink);
    assert.equal(await evaluate('document.getElementById("status").value'), "failed");
    assert.equal(await evaluate('document.getElementById("stage").value'), "verification");
    assert.ok(await evaluate('document.querySelectorAll("#rows details").length > 0'));
    assert.ok(await evaluate('document.querySelectorAll("#rows .diagnostic pre").length > 0'));
    const targetId = await evaluate('document.querySelector("#actions a").getAttribute("href")');
    await evaluate('document.querySelector("#actions a").click()');
    await until('document.getElementById("requirement-details").open && document.querySelector("#rows details")?.open');
    assert.ok(targetId.includes("req="));
    await send("Page.reload");
    await until('document.getElementById("requirement-details")?.open && document.querySelector("#rows details")?.open');
    await screenshot("contract");
    await evaluate('document.querySelector("a[data-view=all]").click()');
    await until('document.getElementById("catalog-details").open && location.hash === "#all"');
    await evaluate('history.back()');
    await until('document.querySelector("#rows details")?.open && location.hash.includes("req=" )');
    await evaluate('history.forward()');
    await until('location.hash === "#all" && document.getElementById("catalog-details").open');
    await screenshot("full");
    const missingScope = data.registry.scopes.find(scope => complete &&
      !data.cohorts[cohort].scopes.some(item => item.id === scope.id));
    if (missingScope) {
      await choose("scope", missingScope.id);
      assert.equal(await text("remaining"), "—");
      assert.equal(await evaluate('document.querySelectorAll(".chart svg").length'), 0);
      assert.match(await text("notice"), /not included/);
    }
    await choose("scope", "all"); await choose("cohort", "current-plan");
    assert.equal(await text("remaining"), String(data.registry.requirements.length));
    const decisions = data.registry.requirements.filter(r => r.state === "needs_decision").length;
    assert.equal(await text("decisions"), String(decisions));
    await choose("status", "decision");
    assert.equal(await evaluate('document.querySelectorAll("#rows details").length'), decisions);
    if (decisions) {
      await evaluate('document.querySelector("#attention a").click()');
      await until('document.querySelector("#rows details")?.open');
      assert.equal(await evaluate('document.querySelector("#rows details").open'), true);
    }
    await choose("search", ""); await choose("status", "all"); await choose("cohort", cohort);
    if (complete?.results.some(r => r.status === "FAIL")) {
      await choose("status", "failed");
      assert.ok(await evaluate('document.querySelectorAll("#rows details").length') > 0);
      await evaluate('document.querySelector("#rows details").open = true');
      assert.ok(await evaluate('!!document.querySelector("#rows details a[href$=\\".json\\"]")'));
    }
    await choose("op-search", "llvm.add");
    assert.ok(await evaluate('document.querySelectorAll("#operations tr").length') > 0);
    await choose("op-search", "");
    await evaluate('document.getElementById("more-ops").click()');
    assert.equal(await evaluate('document.querySelectorAll("#operations tr").length'), data.catalog.operations.length);
    const downloads = await evaluate('[...document.querySelectorAll("a[href^=\\"data/\\"]")].map(a => a.getAttribute("href"))');
    for (const file of downloads) assert.ok(fs.statSync(path.join(site, file)).isFile(), "Missing download: " + file);
    await evaluate('document.querySelector("a[data-view=llvm]").click()');
    await until('location.hash === "#llvm" && document.getElementById("scope").value === "llvm-compat"');
    await send("Emulation.setDeviceMetricsOverride", {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
    await evaluate('window.scrollTo(0, 0)');
    assert.ok(await evaluate('document.documentElement.scrollWidth <= document.documentElement.clientWidth'), "Mobile page overflows horizontally");
    await screenshot("mobile");
    assert.deepEqual(errors, [], "Browser exceptions");
    console.log(JSON.stringify({browser: (await send("Browser.getVersion", {}, null)).product,
      requirements: data.registry.requirements.length, decisions, operations: data.catalog.operations.length,
      mobile: await evaluate('({viewport: document.documentElement.clientWidth, content: document.documentElement.scrollWidth})'),
      checks: ["baseline", "LLVM parsing", "parsing filter reload", "focused views", "filter permalink reload", "contract permalink reload", "back/forward", "missing scope", "current plan", "decisions", "filters", "evidence links", "mobile layout"],
      screenshots: screenshots || null}));
  } catch (error) {
    error.message += "\nChromium stderr (tail):\n" + stderr;
    throw error;
  } finally {
    // This process owns this child; never inspect or signal other browser sessions.
    closing = true;
    if (!transportError) { try { await send("Browser.close", {}, null); } catch {} }
    const timer = setTimeout(() => browser.kill("SIGKILL"), 5000);
    await closed; clearTimeout(timer);
    for (const job of pending.values()) clearTimeout(job.timer);
    fs.rmSync(profile, {recursive: true, force: true});
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
