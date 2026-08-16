// polymorphic-handler-registry.js
// WALL: There's more than one way to handle a message

class PolymorphicHandlerRegistry {
  constructor() {
    this.handlers = new Map();
    this.middleware = [];
  }

  // Accept handlers in ANY style - normalize at registration
  register(eventPattern, handler, context = null) {
    const normalized = this._normalizeHandler(handler, context);
    const pattern = this._compilePattern(eventPattern);
    
    if (!this.handlers.has(eventPattern)) {
      this.handlers.set(eventPattern, []);
    }
    
    this.handlers.get(eventPattern).push({
      pattern,
      execute: normalized,
      raw: handler,
      context
    });
    
    return () => this.unregister(eventPattern, handler);
  }

  _normalizeHandler(handler, context) {
    // Duck-type detection - WALL style
    if (typeof handler === 'function') {
      const isAsync = handler.constructor.name === 'AsyncFunction';
      return async (msg) => {
        const result = context ? handler.call(context, msg) : handler(msg);
        return isAsync ? result : Promise.resolve(result);
      };
    }
    
    if (handler?.handle) {
      return async (msg) => handler.handle(msg);
    }
    
    if (handler?.then) {
      return async (msg) => handler;
    }
    
    throw new Error('Handler must be function, {handle()}, or Promise');
  }

  _compilePattern(pattern) {
    if (pattern instanceof RegExp) return pattern;
    if (typeof pattern === 'string') {
      // Convert glob-style to regex - pragmatic glue
      const regex = pattern
        .replace(/\*/g, '.*')
        .replace(/\?/g, '.')
        .replace(/\//g, '\\/');
      return new RegExp(`^${regex}$`);
    }
    return pattern; // Assume it's a matcher function
  }

  async dispatch(event, payload) {
    const matches = [];
    
    for (const [pattern, handlers] of this.handlers) {
      for (const {pattern: regex, execute} of handlers) {
        if (this._matches(event, regex)) {
          matches.push(execute({event, payload, pattern}));
        }
      }
    }
    
    return await Promise.allSettled(matches);
  }

  _matches(event, pattern) {
    if (pattern instanceof RegExp) return pattern.test(event);
    if (typeof pattern === 'function') return pattern(event);
    return event === pattern;
  }

  unregister(eventPattern, handler) {
    const list = this.handlers.get(eventPattern);
    if (list) {
      const idx = list.findIndex(h => h.raw === handler);
      if (idx >= 0) list.splice(idx, 1);
    }
  }
}

export default new PolymorphicHandlerRegistry();