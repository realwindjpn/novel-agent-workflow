/* web/zip.js — zero-dependency stored-method (0) ZIP codec for creative
 * workspace backups. Encodes/decodes UTF-8 names and content, validates
 * CRC32, rejects traversal/absolute/drive paths, encryption, unsupported
 * compression, excessive entry counts, and oversized expansions.
 *
 * Exposes window.NWZip = { encode, decode, validateName, crc32 }.
 * Also exports via module.exports for Node tests.
 */
(function () {
  "use strict";

  var MAX_ENTRIES = 256;
  var MAX_EXPANDED = 16 * 1024 * 1024; // 16 MiB
  var SIG_LOCAL = 0x04034b50;
  var SIG_CENTRAL = 0x02014b50;
  var SIG_EOCD = 0x06054b50;
  var FLAG_UTF8 = 0x0800;

  var encoder = new TextEncoder();
  var decoder = new TextDecoder();

  function validateName(name) {
    if (!name || typeof name !== "string") throw new Error("unsafe ZIP path");
    if (name[0] === "/" || /^[A-Za-z]:/.test(name)) throw new Error("unsafe ZIP path");
    var parts = name.replace(/\\/g, "/").split("/");
    if (parts.some(function (p) { return p === ".." || p === ""; })) {
      throw new Error("unsafe ZIP path");
    }
    if (parts[0] !== "creative-backup") throw new Error("unexpected ZIP root");
    return parts.join("/");
  }

  var CRC_TABLE = (function () {
    var t = new Uint32Array(256);
    for (var n = 0; n < 256; n++) {
      var c = n;
      for (var k = 0; k < 8; k++) {
        c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      }
      t[n] = c >>> 0;
    }
    return t;
  })();

  function crc32(bytes) {
    var view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    var c = 0xFFFFFFFF;
    for (var i = 0; i < view.length; i++) {
      c = CRC_TABLE[(c ^ view[i]) & 0xFF] ^ (c >>> 8);
    }
    return (c ^ 0xFFFFFFFF) >>> 0;
  }

  function encode(entries) {
    var keys = Object.keys(entries);
    if (keys.length > MAX_ENTRIES) throw new Error("too many ZIP entries (max " + MAX_ENTRIES + ")");
    var chunks = [];
    var central = [];
    var offset = 0;

    keys.forEach(function (rawName) {
      var name = validateName(rawName);
      var nameBytes = encoder.encode(name);
      var data = encoder.encode(String(entries[rawName]));
      if (data.length > MAX_EXPANDED) throw new Error("ZIP entry too large");
      var crc = crc32(data);

      var local = new Uint8Array(30 + nameBytes.length + data.length);
      var dv = new DataView(local.buffer);
      dv.setUint32(0, SIG_LOCAL, true);
      dv.setUint16(4, 20, true);          // version needed
      dv.setUint16(6, FLAG_UTF8, true);   // flags: UTF-8 names
      dv.setUint16(8, 0, true);           // method: stored
      dv.setUint16(10, 0, true);          // mod time
      dv.setUint16(12, 0, true);          // mod date
      dv.setUint32(14, crc, true);
      dv.setUint32(18, data.length, true);   // compressed size
      dv.setUint32(22, data.length, true);   // uncompressed size
      dv.setUint16(26, nameBytes.length, true);
      dv.setUint16(28, 0, true);          // extra length
      local.set(nameBytes, 30);
      local.set(data, 30 + nameBytes.length);

      chunks.push(local);

      var cd = new Uint8Array(46 + nameBytes.length);
      var cdv = new DataView(cd.buffer);
      cdv.setUint32(0, SIG_CENTRAL, true);
      cdv.setUint16(4, 20, true);         // version made by
      cdv.setUint16(6, 20, true);         // version needed
      cdv.setUint16(8, FLAG_UTF8, true);  // flags
      cdv.setUint16(10, 0, true);         // method
      cdv.setUint16(12, 0, true);         // mod time
      cdv.setUint16(14, 0, true);         // mod date
      cdv.setUint32(16, crc, true);
      cdv.setUint32(20, data.length, true);
      cdv.setUint32(24, data.length, true);
      cdv.setUint16(28, nameBytes.length, true);
      cdv.setUint16(30, 0, true);         // extra
      cdv.setUint16(32, 0, true);         // comment
      cdv.setUint16(34, 0, true);         // disk start
      cdv.setUint16(36, 0, true);         // internal attrs
      cdv.setUint32(38, 0, true);         // external attrs
      cdv.setUint32(42, offset, true);    // local header offset
      cd.set(nameBytes, 46);
      central.push(cd);

      offset += local.length;
    });

    var centralBytes = concat(central);
    var eocd = new Uint8Array(22);
    var ev = new DataView(eocd.buffer);
    ev.setUint32(0, SIG_EOCD, true);
    ev.setUint16(4, 0, true);
    ev.setUint16(6, 0, true);
    ev.setUint16(8, keys.length, true);
    ev.setUint16(10, keys.length, true);
    ev.setUint32(12, centralBytes.length, true);
    ev.setUint32(16, offset, true);
    ev.setUint16(20, 0, true);

    return concat([].concat(chunks, [centralBytes], [eocd]));
  }

  function concat(arrs) {
    var total = 0;
    for (var i = 0; i < arrs.length; i++) total += arrs[i].length;
    var out = new Uint8Array(total);
    var p = 0;
    for (var j = 0; j < arrs.length; j++) { out.set(arrs[j], p); p += arrs[j].length; }
    return out;
  }

  function findEocd(bytes) {
    // Scan backwards for EOCD signature (max 64KB comment).
    var min = Math.max(0, bytes.length - (22 + 65535));
    for (var i = bytes.length - 22; i >= min; i--) {
      if (bytes[i] === 0x50 && bytes[i + 1] === 0x4b && bytes[i + 2] === 0x05 && bytes[i + 3] === 0x06) {
        return i;
      }
    }
    throw new Error("ZIP end-of-central-directory not found");
  }

  function decode(bytes) {
    var view = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    if (view.length < 22) throw new Error("ZIP too small");
    var eocd = findEocd(view);
    var dv = new DataView(view.buffer, view.byteOffset, view.byteLength);
    var totalEntries = dv.getUint16(eocd + 10, true);
    if (totalEntries > MAX_ENTRIES) throw new Error("too many ZIP entries (max " + MAX_ENTRIES + ")");
    var cdSize = dv.getUint32(eocd + 12, true);
    var cdOffset = dv.getUint32(eocd + 16, true);

    var entries = {};
    var expanded = 0;
    var p = cdOffset;
    for (var n = 0; n < totalEntries; n++) {
      if (dv.getUint32(p, true) !== SIG_CENTRAL) throw new Error("bad central directory entry");
      var flags = dv.getUint16(p + 8, true);
      var method = dv.getUint16(p + 10, true);
      var crc = dv.getUint32(p + 16, true);
      var compSize = dv.getUint32(p + 20, true);
      var uncompSize = dv.getUint32(p + 24, true);
      var nameLen = dv.getUint16(p + 28, true);
      var extraLen = dv.getUint16(p + 30, true);
      var commentLen = dv.getUint16(p + 32, true);
      var localOffset = dv.getUint32(p + 42, true);
      var nameBytes = view.subarray(p + 46, p + 46 + nameLen);
      var name = decoder.decode(nameBytes);
      var validated = validateName(name);

      if (flags & 0x01) throw new Error("encrypted ZIP entries are unsupported");
      if (method !== 0) throw new Error("unsupported compression method " + method);
      expanded += uncompSize;
      if (expanded > MAX_EXPANDED) throw new Error("ZIP expansion too large (max 16 MiB)");

      // Read local header to locate data.
      if (dv.getUint32(localOffset, true) !== SIG_LOCAL) throw new Error("bad local header");
      var lNameLen = dv.getUint16(localOffset + 26, true);
      var lExtraLen = dv.getUint16(localOffset + 28, true);
      var dataStart = localOffset + 30 + lNameLen + lExtraLen;
      var data = view.subarray(dataStart, dataStart + compSize);

      // Validate CRC32.
      if (crc32(data) !== crc) throw new Error("ZIP CRC mismatch for " + validated);

      entries[validated] = decoder.decode(data);
      p += 46 + nameLen + extraLen + commentLen;
    }
    return entries;
  }

  var api = {
    encode: encode,
    decode: decode,
    validateName: validateName,
    crc32: crc32,
    MAX_ENTRIES: MAX_ENTRIES,
    MAX_EXPANDED: MAX_EXPANDED
  };
  if (typeof window !== "undefined") window.NWZip = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
