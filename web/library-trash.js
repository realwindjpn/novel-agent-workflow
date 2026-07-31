(function () {
  "use strict";

  function cloneState(state) {
    return {
      library: state.library,
      trash: state.trash.slice(),
      selected: state.selected,
      pending: state.pending,
      busy: state.busy,
      error: state.error,
    };
  }

  function createController(options) {
    var state = {
      library: "", trash: [], selected: null,
      pending: null, busy: false, error: ""
    };

    function emit() {
      if (options.onChange) options.onChange(cloneState(state));
    }

    function snapshot() { return cloneState(state); }

    function select(book) {
      if (state.busy) return snapshot();
      state.selected = book || null;
      emit();
      return snapshot();
    }

    function requestTrash() {
      if (state.busy || !state.selected) return snapshot();
      state.pending = state.selected;
      state.error = "";
      emit();
      return snapshot();
    }

    function cancelTrash() {
      if (!state.busy) state.pending = null;
      emit();
      return snapshot();
    }

    function refresh() {
      return Promise.resolve(options.listTrash()).then(function (payload) {
        state.library = payload && payload.library ? payload.library : "";
        state.trash = payload && Array.isArray(payload.trash) ? payload.trash.slice() : [];
        state.error = "";
        emit();
        return snapshot();
      }).catch(function (error) {
        state.error = (error && error.message) || String(error);
        emit();
        throw error;
      });
    }

    function runMutation(kind, operation) {
      if (state.busy) return Promise.reject(new Error("recycle operation already running"));
      state.busy = true;
      state.error = "";
      emit();
      return Promise.resolve(operation()).then(function (result) {
        return Promise.resolve(options.onMutation ? options.onMutation(result, kind) : null)
          .then(function () { return refresh(); })
          .then(function () { return result; });
      }).catch(function (error) {
        state.error = (error && error.message) || String(error);
        emit();
        throw error;
      }).finally(function () {
        state.busy = false;
        emit();
      });
    }

    function confirmTrash() {
      if (!state.pending) return Promise.reject(new Error("no book selected for recycle"));
      var directory = state.pending.directory;
      state.pending = null;
      return runMutation("trash", function () {
        return options.trashBook(directory);
      }).then(function (result) {
        state.selected = null;
        emit();
        return result;
      });
    }

    function restore(trashId) {
      return runMutation("restore", function () {
        return options.restoreBook(trashId);
      });
    }

    emit();
    return {
      snapshot: snapshot,
      select: select,
      requestTrash: requestTrash,
      cancelTrash: cancelTrash,
      confirmTrash: confirmTrash,
      restore: restore,
      refresh: refresh,
    };
  }

  var api = { createController: createController };
  if (typeof window !== "undefined") window.NWLibraryTrash = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
