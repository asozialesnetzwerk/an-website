(function webpackUniversalModuleDefinition(root, factory) {
	if(typeof exports === 'object' && typeof module === 'object')
		module.exports = factory();
	else if(typeof define === 'function' && define.amd)
		define([], factory);
	else if(typeof exports === 'object')
		exports["elastic-apm-rum"] = factory();
	else
		root["elastic-apm-rum"] = factory();
})(self, function() {
return /******/ (function() { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "../rum-core/dist/es/bootstrap.js":
/*!****************************************!*\
  !*** ../rum-core/dist/es/bootstrap.js ***!
  \****************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "bootstrap": function() { return /* binding */ bootstrap; }
/* harmony export */ });
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _common_patching__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./common/patching */ "../rum-core/dist/es/common/patching/index.js");
/* harmony import */ var _state__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./state */ "../rum-core/dist/es/state.js");



var enabled = false;
function bootstrap() {
  if ((0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.isPlatformSupported)()) {
    (0,_common_patching__WEBPACK_IMPORTED_MODULE_1__.patchAll)();
    _state__WEBPACK_IMPORTED_MODULE_2__.state.bootstrapTime = (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.now)();
    enabled = true;
  } else if (_common_utils__WEBPACK_IMPORTED_MODULE_0__.isBrowser) {
    console.log('[Elastic APM] platform is not supported!');
  }

  return enabled;
}

/***/ }),

/***/ "../rum-core/dist/es/common/after-frame.js":
/*!*************************************************!*\
  !*** ../rum-core/dist/es/common/after-frame.js ***!
  \*************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": function() { return /* binding */ afterFrame; }
/* harmony export */ });
var RAF_TIMEOUT = 100;
function afterFrame(callback) {
  var handler = function handler() {
    clearTimeout(timeout);
    cancelAnimationFrame(raf);
    setTimeout(callback);
  };

  var timeout = setTimeout(handler, RAF_TIMEOUT);
  var raf = requestAnimationFrame(handler);
}

/***/ }),

/***/ "../rum-core/dist/es/common/apm-server.js":
/*!************************************************!*\
  !*** ../rum-core/dist/es/common/apm-server.js ***!
  \************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _queue__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./queue */ "../rum-core/dist/es/common/queue.js");
/* harmony import */ var _throttle__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./throttle */ "../rum-core/dist/es/common/throttle.js");
/* harmony import */ var _ndjson__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./ndjson */ "../rum-core/dist/es/common/ndjson.js");
/* harmony import */ var _truncate__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./truncate */ "../rum-core/dist/es/common/truncate.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _polyfills__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./polyfills */ "../rum-core/dist/es/common/polyfills.js");
/* harmony import */ var _compress__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./compress */ "../rum-core/dist/es/common/compress.js");
/* harmony import */ var _state__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../state */ "../rum-core/dist/es/state.js");
/* harmony import */ var _http_fetch__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./http/fetch */ "../rum-core/dist/es/common/http/fetch.js");
/* harmony import */ var _http_xhr__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./http/xhr */ "../rum-core/dist/es/common/http/xhr.js");











var THROTTLE_INTERVAL = 60000;

var ApmServer = function () {
  function ApmServer(configService, loggingService) {
    this._configService = configService;
    this._loggingService = loggingService;
    this.queue = undefined;
    this.throttleEvents = _utils__WEBPACK_IMPORTED_MODULE_0__.noop;
  }

  var _proto = ApmServer.prototype;

  _proto.init = function init() {
    var _this = this;

    var queueLimit = this._configService.get('queueLimit');

    var flushInterval = this._configService.get('flushInterval');

    var limit = this._configService.get('eventsLimit');

    var onFlush = function onFlush(events) {
      var promise = _this.sendEvents(events);

      if (promise) {
        promise.catch(function (reason) {
          _this._loggingService.warn('Failed sending events!', _this._constructError(reason));
        });
      }
    };

    this.queue = new _queue__WEBPACK_IMPORTED_MODULE_1__.default(onFlush, {
      queueLimit: queueLimit,
      flushInterval: flushInterval
    });
    this.throttleEvents = (0,_throttle__WEBPACK_IMPORTED_MODULE_2__.default)(this.queue.add.bind(this.queue), function () {
      return _this._loggingService.warn('Dropped events due to throttling!');
    }, {
      limit: limit,
      interval: THROTTLE_INTERVAL
    });

    this._configService.observeEvent(_constants__WEBPACK_IMPORTED_MODULE_3__.QUEUE_FLUSH, function () {
      _this.queue.flush();
    });
  };

  _proto._postJson = function _postJson(endPoint, payload) {
    var _this2 = this;

    var headers = {
      'Content-Type': 'application/x-ndjson'
    };

    var apmRequest = this._configService.get('apmRequest');

    var params = {
      payload: payload,
      headers: headers,
      beforeSend: apmRequest
    };
    return (0,_compress__WEBPACK_IMPORTED_MODULE_4__.compressPayload)(params).catch(function (error) {
      if (_state__WEBPACK_IMPORTED_MODULE_5__.__DEV__) {
        _this2._loggingService.debug('Compressing the payload using CompressionStream API failed', error.message);
      }

      return params;
    }).then(function (result) {
      return _this2._makeHttpRequest('POST', endPoint, result);
    }).then(function (_ref) {
      var responseText = _ref.responseText;
      return responseText;
    });
  };

  _proto._constructError = function _constructError(reason) {
    var url = reason.url,
        status = reason.status,
        responseText = reason.responseText;

    if (typeof status == 'undefined') {
      return reason;
    }

    var message = url + ' HTTP status: ' + status;

    if (_state__WEBPACK_IMPORTED_MODULE_5__.__DEV__ && responseText) {
      try {
        var serverErrors = [];
        var response = JSON.parse(responseText);

        if (response.errors && response.errors.length > 0) {
          response.errors.forEach(function (err) {
            return serverErrors.push(err.message);
          });
          message += ' ' + serverErrors.join(',');
        }
      } catch (e) {
        this._loggingService.debug('Error parsing response from APM server', e);
      }
    }

    return new Error(message);
  };

  _proto._makeHttpRequest = function _makeHttpRequest(method, url, _temp) {
    var _ref2 = _temp === void 0 ? {} : _temp,
        _ref2$timeout = _ref2.timeout,
        timeout = _ref2$timeout === void 0 ? _constants__WEBPACK_IMPORTED_MODULE_3__.HTTP_REQUEST_TIMEOUT : _ref2$timeout,
        payload = _ref2.payload,
        headers = _ref2.headers,
        beforeSend = _ref2.beforeSend;

    var sendCredentials = this._configService.get('sendCredentials');

    if (!beforeSend && (0,_http_fetch__WEBPACK_IMPORTED_MODULE_6__.shouldUseFetchWithKeepAlive)(method, payload)) {
      return (0,_http_fetch__WEBPACK_IMPORTED_MODULE_6__.sendFetchRequest)(method, url, {
        keepalive: true,
        timeout: timeout,
        payload: payload,
        headers: headers,
        sendCredentials: sendCredentials
      }).catch(function (reason) {
        if (reason instanceof TypeError) {
          return (0,_http_xhr__WEBPACK_IMPORTED_MODULE_7__.sendXHR)(method, url, {
            timeout: timeout,
            payload: payload,
            headers: headers,
            beforeSend: beforeSend,
            sendCredentials: sendCredentials
          });
        }

        throw reason;
      });
    }

    return (0,_http_xhr__WEBPACK_IMPORTED_MODULE_7__.sendXHR)(method, url, {
      timeout: timeout,
      payload: payload,
      headers: headers,
      beforeSend: beforeSend,
      sendCredentials: sendCredentials
    });
  };

  _proto.fetchConfig = function fetchConfig(serviceName, environment) {
    var _this3 = this;

    var _this$getEndpoints = this.getEndpoints(),
        configEndpoint = _this$getEndpoints.configEndpoint;

    if (!serviceName) {
      return _polyfills__WEBPACK_IMPORTED_MODULE_8__.Promise.reject('serviceName is required for fetching central config.');
    }

    configEndpoint += "?service.name=" + serviceName;

    if (environment) {
      configEndpoint += "&service.environment=" + environment;
    }

    var localConfig = this._configService.getLocalConfig();

    if (localConfig) {
      configEndpoint += "&ifnonematch=" + localConfig.etag;
    }

    var apmRequest = this._configService.get('apmRequest');

    return this._makeHttpRequest('GET', configEndpoint, {
      timeout: 5000,
      beforeSend: apmRequest
    }).then(function (xhr) {
      var status = xhr.status,
          responseText = xhr.responseText;

      if (status === 304) {
        return localConfig;
      } else {
        var remoteConfig = JSON.parse(responseText);
        var etag = xhr.getResponseHeader('etag');

        if (etag) {
          remoteConfig.etag = etag.replace(/["]/g, '');

          _this3._configService.setLocalConfig(remoteConfig, true);
        }

        return remoteConfig;
      }
    }).catch(function (reason) {
      var error = _this3._constructError(reason);

      return _polyfills__WEBPACK_IMPORTED_MODULE_8__.Promise.reject(error);
    });
  };

  _proto.createMetaData = function createMetaData() {
    var cfg = this._configService;
    var metadata = {
      service: {
        name: cfg.get('serviceName'),
        version: cfg.get('serviceVersion'),
        agent: {
          name: 'rum-js',
          version: cfg.version
        },
        language: {
          name: 'javascript'
        },
        environment: cfg.get('environment')
      },
      labels: cfg.get('context.tags')
    };
    return (0,_truncate__WEBPACK_IMPORTED_MODULE_9__.truncateModel)(_truncate__WEBPACK_IMPORTED_MODULE_9__.METADATA_MODEL, metadata);
  };

  _proto.addError = function addError(error) {
    var _this$throttleEvents;

    this.throttleEvents((_this$throttleEvents = {}, _this$throttleEvents[_constants__WEBPACK_IMPORTED_MODULE_3__.ERRORS] = error, _this$throttleEvents));
  };

  _proto.addTransaction = function addTransaction(transaction) {
    var _this$throttleEvents2;

    this.throttleEvents((_this$throttleEvents2 = {}, _this$throttleEvents2[_constants__WEBPACK_IMPORTED_MODULE_3__.TRANSACTIONS] = transaction, _this$throttleEvents2));
  };

  _proto.ndjsonErrors = function ndjsonErrors(errors, compress) {
    var key = compress ? 'e' : 'error';
    return errors.map(function (error) {
      var _NDJSON$stringify;

      return _ndjson__WEBPACK_IMPORTED_MODULE_10__.default.stringify((_NDJSON$stringify = {}, _NDJSON$stringify[key] = compress ? (0,_compress__WEBPACK_IMPORTED_MODULE_4__.compressError)(error) : error, _NDJSON$stringify));
    });
  };

  _proto.ndjsonMetricsets = function ndjsonMetricsets(metricsets) {
    return metricsets.map(function (metricset) {
      return _ndjson__WEBPACK_IMPORTED_MODULE_10__.default.stringify({
        metricset: metricset
      });
    }).join('');
  };

  _proto.ndjsonTransactions = function ndjsonTransactions(transactions, compress) {
    var _this4 = this;

    var key = compress ? 'x' : 'transaction';
    return transactions.map(function (tr) {
      var _NDJSON$stringify2;

      var spans = '',
          breakdowns = '';

      if (!compress) {
        if (tr.spans) {
          spans = tr.spans.map(function (span) {
            return _ndjson__WEBPACK_IMPORTED_MODULE_10__.default.stringify({
              span: span
            });
          }).join('');
          delete tr.spans;
        }

        if (tr.breakdown) {
          breakdowns = _this4.ndjsonMetricsets(tr.breakdown);
          delete tr.breakdown;
        }
      }

      return _ndjson__WEBPACK_IMPORTED_MODULE_10__.default.stringify((_NDJSON$stringify2 = {}, _NDJSON$stringify2[key] = compress ? (0,_compress__WEBPACK_IMPORTED_MODULE_4__.compressTransaction)(tr) : tr, _NDJSON$stringify2)) + spans + breakdowns;
    });
  };

  _proto.sendEvents = function sendEvents(events) {
    var _payload, _NDJSON$stringify3;

    if (events.length === 0) {
      return;
    }

    var transactions = [];
    var errors = [];

    for (var i = 0; i < events.length; i++) {
      var event = events[i];

      if (event[_constants__WEBPACK_IMPORTED_MODULE_3__.TRANSACTIONS]) {
        transactions.push(event[_constants__WEBPACK_IMPORTED_MODULE_3__.TRANSACTIONS]);
      }

      if (event[_constants__WEBPACK_IMPORTED_MODULE_3__.ERRORS]) {
        errors.push(event[_constants__WEBPACK_IMPORTED_MODULE_3__.ERRORS]);
      }
    }

    if (transactions.length === 0 && errors.length === 0) {
      return;
    }

    var cfg = this._configService;
    var payload = (_payload = {}, _payload[_constants__WEBPACK_IMPORTED_MODULE_3__.TRANSACTIONS] = transactions, _payload[_constants__WEBPACK_IMPORTED_MODULE_3__.ERRORS] = errors, _payload);
    var filteredPayload = cfg.applyFilters(payload);

    if (!filteredPayload) {
      this._loggingService.warn('Dropped payload due to filtering!');

      return;
    }

    var apiVersion = cfg.get('apiVersion');
    var compress = apiVersion > 2;
    var ndjson = [];
    var metadata = this.createMetaData();
    var metadataKey = compress ? 'm' : 'metadata';
    ndjson.push(_ndjson__WEBPACK_IMPORTED_MODULE_10__.default.stringify((_NDJSON$stringify3 = {}, _NDJSON$stringify3[metadataKey] = compress ? (0,_compress__WEBPACK_IMPORTED_MODULE_4__.compressMetadata)(metadata) : metadata, _NDJSON$stringify3)));
    ndjson = ndjson.concat(this.ndjsonErrors(filteredPayload[_constants__WEBPACK_IMPORTED_MODULE_3__.ERRORS], compress), this.ndjsonTransactions(filteredPayload[_constants__WEBPACK_IMPORTED_MODULE_3__.TRANSACTIONS], compress));
    var ndjsonPayload = ndjson.join('');

    var _this$getEndpoints2 = this.getEndpoints(),
        intakeEndpoint = _this$getEndpoints2.intakeEndpoint;

    return this._postJson(intakeEndpoint, ndjsonPayload);
  };

  _proto.getEndpoints = function getEndpoints() {
    var serverUrl = this._configService.get('serverUrl');

    var apiVersion = this._configService.get('apiVersion');

    var serverUrlPrefix = this._configService.get('serverUrlPrefix') || "/intake/v" + apiVersion + "/rum/events";
    var intakeEndpoint = serverUrl + serverUrlPrefix;
    var configEndpoint = serverUrl + "/config/v1/rum/agents";
    return {
      intakeEndpoint: intakeEndpoint,
      configEndpoint: configEndpoint
    };
  };

  return ApmServer;
}();

/* harmony default export */ __webpack_exports__["default"] = (ApmServer);

/***/ }),

/***/ "../rum-core/dist/es/common/compress.js":
/*!**********************************************!*\
  !*** ../rum-core/dist/es/common/compress.js ***!
  \**********************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "compressMetadata": function() { return /* binding */ compressMetadata; },
/* harmony export */   "compressTransaction": function() { return /* binding */ compressTransaction; },
/* harmony export */   "compressError": function() { return /* binding */ compressError; },
/* harmony export */   "compressMetricsets": function() { return /* binding */ compressMetricsets; },
/* harmony export */   "compressPayload": function() { return /* binding */ compressPayload; }
/* harmony export */ });
/* harmony import */ var _polyfills__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./polyfills */ "../rum-core/dist/es/common/polyfills.js");
/* harmony import */ var _performance_monitoring_capture_navigation__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../performance-monitoring/capture-navigation */ "../rum-core/dist/es/performance-monitoring/capture-navigation.js");
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./utils */ "../rum-core/dist/es/common/utils.js");




function compressStackFrames(frames) {
  return frames.map(function (frame) {
    return {
      ap: frame.abs_path,
      f: frame.filename,
      fn: frame.function,
      li: frame.lineno,
      co: frame.colno
    };
  });
}

function compressResponse(response) {
  return {
    ts: response.transfer_size,
    ebs: response.encoded_body_size,
    dbs: response.decoded_body_size
  };
}

function compressHTTP(http) {
  var compressed = {};
  var method = http.method,
      status_code = http.status_code,
      url = http.url,
      response = http.response;
  compressed.url = url;

  if (method) {
    compressed.mt = method;
  }

  if (status_code) {
    compressed.sc = status_code;
  }

  if (response) {
    compressed.r = compressResponse(response);
  }

  return compressed;
}

function compressContext(context) {
  if (!context) {
    return null;
  }

  var compressed = {};
  var page = context.page,
      http = context.http,
      response = context.response,
      destination = context.destination,
      user = context.user,
      custom = context.custom;

  if (page) {
    compressed.p = {
      rf: page.referer,
      url: page.url
    };
  }

  if (http) {
    compressed.h = compressHTTP(http);
  }

  if (response) {
    compressed.r = compressResponse(response);
  }

  if (destination) {
    var service = destination.service;
    compressed.dt = {
      se: {
        n: service.name,
        t: service.type,
        rc: service.resource
      },
      ad: destination.address,
      po: destination.port
    };
  }

  if (user) {
    compressed.u = {
      id: user.id,
      un: user.username,
      em: user.email
    };
  }

  if (custom) {
    compressed.cu = custom;
  }

  return compressed;
}

function compressMarks(marks) {
  if (!marks) {
    return null;
  }

  var compressedNtMarks = compressNavigationTimingMarks(marks.navigationTiming);
  var compressed = {
    nt: compressedNtMarks,
    a: compressAgentMarks(compressedNtMarks, marks.agent)
  };
  return compressed;
}

function compressNavigationTimingMarks(ntMarks) {
  if (!ntMarks) {
    return null;
  }

  var compressed = {};
  _performance_monitoring_capture_navigation__WEBPACK_IMPORTED_MODULE_0__.COMPRESSED_NAV_TIMING_MARKS.forEach(function (mark, index) {
    var mapping = _performance_monitoring_capture_navigation__WEBPACK_IMPORTED_MODULE_0__.NAVIGATION_TIMING_MARKS[index];
    compressed[mark] = ntMarks[mapping];
  });
  return compressed;
}

function compressAgentMarks(compressedNtMarks, agentMarks) {
  var compressed = {};

  if (compressedNtMarks) {
    compressed = {
      fb: compressedNtMarks.rs,
      di: compressedNtMarks.di,
      dc: compressedNtMarks.dc
    };
  }

  if (agentMarks) {
    var fp = agentMarks.firstContentfulPaint;
    var lp = agentMarks.largestContentfulPaint;

    if (fp) {
      compressed.fp = fp;
    }

    if (lp) {
      compressed.lp = lp;
    }
  }

  if (Object.keys(compressed).length === 0) {
    return null;
  }

  return compressed;
}

function compressMetadata(metadata) {
  var service = metadata.service,
      labels = metadata.labels;
  var agent = service.agent,
      language = service.language;
  return {
    se: {
      n: service.name,
      ve: service.version,
      a: {
        n: agent.name,
        ve: agent.version
      },
      la: {
        n: language.name
      },
      en: service.environment
    },
    l: labels
  };
}
function compressTransaction(transaction) {
  var spans = transaction.spans.map(function (span) {
    var spanData = {
      id: span.id,
      n: span.name,
      t: span.type,
      s: span.start,
      d: span.duration,
      c: compressContext(span.context),
      o: span.outcome,
      sr: span.sample_rate
    };

    if (span.parent_id !== transaction.id) {
      spanData.pid = span.parent_id;
    }

    if (span.sync === true) {
      spanData.sy = true;
    }

    if (span.subtype) {
      spanData.su = span.subtype;
    }

    if (span.action) {
      spanData.ac = span.action;
    }

    return spanData;
  });
  var tr = {
    id: transaction.id,
    tid: transaction.trace_id,
    n: transaction.name,
    t: transaction.type,
    d: transaction.duration,
    c: compressContext(transaction.context),
    k: compressMarks(transaction.marks),
    me: compressMetricsets(transaction.breakdown),
    y: spans,
    yc: {
      sd: spans.length
    },
    sm: transaction.sampled,
    sr: transaction.sample_rate,
    o: transaction.outcome
  };

  if (transaction.experience) {
    var _transaction$experien = transaction.experience,
        cls = _transaction$experien.cls,
        fid = _transaction$experien.fid,
        tbt = _transaction$experien.tbt,
        longtask = _transaction$experien.longtask;
    tr.exp = {
      cls: cls,
      fid: fid,
      tbt: tbt,
      lt: longtask
    };
  }

  if (transaction.session) {
    var _transaction$session = transaction.session,
        id = _transaction$session.id,
        sequence = _transaction$session.sequence;
    tr.ses = {
      id: id,
      seq: sequence
    };
  }

  return tr;
}
function compressError(error) {
  var exception = error.exception;
  var compressed = {
    id: error.id,
    cl: error.culprit,
    ex: {
      mg: exception.message,
      st: compressStackFrames(exception.stacktrace),
      t: error.type
    },
    c: compressContext(error.context)
  };
  var transaction = error.transaction;

  if (transaction) {
    compressed.tid = error.trace_id;
    compressed.pid = error.parent_id;
    compressed.xid = error.transaction_id;
    compressed.x = {
      t: transaction.type,
      sm: transaction.sampled
    };
  }

  return compressed;
}
function compressMetricsets(breakdowns) {
  return breakdowns.map(function (_ref) {
    var span = _ref.span,
        samples = _ref.samples;
    var isSpan = span != null;

    if (isSpan) {
      return {
        y: {
          t: span.type
        },
        sa: {
          ysc: {
            v: samples['span.self_time.count'].value
          },
          yss: {
            v: samples['span.self_time.sum.us'].value
          }
        }
      };
    }

    return {
      sa: {
        xdc: {
          v: samples['transaction.duration.count'].value
        },
        xds: {
          v: samples['transaction.duration.sum.us'].value
        },
        xbc: {
          v: samples['transaction.breakdown.count'].value
        }
      }
    };
  });
}
function compressPayload(params, type) {
  if (type === void 0) {
    type = 'gzip';
  }

  var isCompressionStreamSupported = typeof CompressionStream === 'function';
  return new _polyfills__WEBPACK_IMPORTED_MODULE_1__.Promise(function (resolve) {
    if (!isCompressionStreamSupported) {
      return resolve(params);
    }

    if ((0,_utils__WEBPACK_IMPORTED_MODULE_2__.isBeaconInspectionEnabled)()) {
      return resolve(params);
    }

    var payload = params.payload,
        headers = params.headers,
        beforeSend = params.beforeSend;
    var payloadStream = new Blob([payload]).stream();
    var compressedStream = payloadStream.pipeThrough(new CompressionStream(type));
    return new Response(compressedStream).blob().then(function (payload) {
      headers['Content-Encoding'] = type;
      return resolve({
        payload: payload,
        headers: headers,
        beforeSend: beforeSend
      });
    });
  });
}

/***/ }),

/***/ "../rum-core/dist/es/common/config-service.js":
/*!****************************************************!*\
  !*** ../rum-core/dist/es/common/config-service.js ***!
  \****************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _event_handler__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./event-handler */ "../rum-core/dist/es/common/event-handler.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./constants */ "../rum-core/dist/es/common/constants.js");
function _extends() {
  _extends = Object.assign || function (target) {
    for (var i = 1; i < arguments.length; i++) {
      var source = arguments[i];

      for (var key in source) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
          target[key] = source[key];
        }
      }
    }

    return target;
  };

  return _extends.apply(this, arguments);
}





function getConfigFromScript() {
  var script = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.getCurrentScript)();
  var config = getDataAttributesFromNode(script);
  return config;
}

function getDataAttributesFromNode(node) {
  if (!node) {
    return {};
  }

  var dataAttrs = {};
  var dataRegex = /^data-([\w-]+)$/;
  var attrs = node.attributes;

  for (var i = 0; i < attrs.length; i++) {
    var attr = attrs[i];

    if (dataRegex.test(attr.nodeName)) {
      var key = attr.nodeName.match(dataRegex)[1];
      var camelCasedkey = key.split('-').map(function (value, index) {
        return index > 0 ? value.charAt(0).toUpperCase() + value.substring(1) : value;
      }).join('');
      dataAttrs[camelCasedkey] = attr.value || attr.nodeValue;
    }
  }

  return dataAttrs;
}

var Config = function () {
  function Config() {
    this.config = {
      serviceName: '',
      serviceVersion: '',
      environment: '',
      serverUrl: 'http://localhost:8200',
      serverUrlPrefix: '',
      active: true,
      instrument: true,
      disableInstrumentations: [],
      logLevel: 'warn',
      breakdownMetrics: false,
      ignoreTransactions: [],
      eventsLimit: 80,
      queueLimit: -1,
      flushInterval: 500,
      distributedTracing: true,
      distributedTracingOrigins: [],
      distributedTracingHeaderName: 'traceparent',
      pageLoadTraceId: '',
      pageLoadSpanId: '',
      pageLoadSampled: false,
      pageLoadTransactionName: '',
      propagateTracestate: false,
      transactionSampleRate: 1.0,
      centralConfig: false,
      monitorLongtasks: true,
      apiVersion: 2,
      context: {},
      session: false,
      apmRequest: null,
      sendCredentials: false
    };
    this.events = new _event_handler__WEBPACK_IMPORTED_MODULE_1__.default();
    this.filters = [];
    this.version = '';
  }

  var _proto = Config.prototype;

  _proto.init = function init() {
    var scriptData = getConfigFromScript();
    this.setConfig(scriptData);
  };

  _proto.setVersion = function setVersion(version) {
    this.version = version;
  };

  _proto.addFilter = function addFilter(cb) {
    if (typeof cb !== 'function') {
      throw new Error('Argument to must be function');
    }

    this.filters.push(cb);
  };

  _proto.applyFilters = function applyFilters(data) {
    for (var i = 0; i < this.filters.length; i++) {
      data = this.filters[i](data);

      if (!data) {
        return;
      }
    }

    return data;
  };

  _proto.get = function get(key) {
    return key.split('.').reduce(function (obj, objKey) {
      return obj && obj[objKey];
    }, this.config);
  };

  _proto.setUserContext = function setUserContext(userContext) {
    if (userContext === void 0) {
      userContext = {};
    }

    var context = {};
    var _userContext = userContext,
        id = _userContext.id,
        username = _userContext.username,
        email = _userContext.email;

    if (typeof id === 'number' || typeof id === 'string') {
      context.id = id;
    }

    if (typeof username === 'string') {
      context.username = username;
    }

    if (typeof email === 'string') {
      context.email = email;
    }

    this.config.context.user = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.extend)(this.config.context.user || {}, context);
  };

  _proto.setCustomContext = function setCustomContext(customContext) {
    if (customContext === void 0) {
      customContext = {};
    }

    this.config.context.custom = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.extend)(this.config.context.custom || {}, customContext);
  };

  _proto.addLabels = function addLabels(tags) {
    var _this = this;

    if (!this.config.context.tags) {
      this.config.context.tags = {};
    }

    var keys = Object.keys(tags);
    keys.forEach(function (k) {
      return (0,_utils__WEBPACK_IMPORTED_MODULE_0__.setLabel)(k, tags[k], _this.config.context.tags);
    });
  };

  _proto.setConfig = function setConfig(properties) {
    if (properties === void 0) {
      properties = {};
    }

    var _properties = properties,
        transactionSampleRate = _properties.transactionSampleRate,
        serverUrl = _properties.serverUrl;

    if (serverUrl) {
      properties.serverUrl = serverUrl.replace(/\/+$/, '');
    }

    if (!(0,_utils__WEBPACK_IMPORTED_MODULE_0__.isUndefined)(transactionSampleRate)) {
      if (transactionSampleRate < 0.0001 && transactionSampleRate > 0) {
        transactionSampleRate = 0.0001;
      }

      properties.transactionSampleRate = Math.round(transactionSampleRate * 10000) / 10000;
    }

    (0,_utils__WEBPACK_IMPORTED_MODULE_0__.merge)(this.config, properties);
    this.events.send(_constants__WEBPACK_IMPORTED_MODULE_2__.CONFIG_CHANGE, [this.config]);
  };

  _proto.validate = function validate(properties) {
    if (properties === void 0) {
      properties = {};
    }

    var requiredKeys = ['serviceName', 'serverUrl'];
    var allKeys = Object.keys(this.config);
    var errors = {
      missing: [],
      invalid: [],
      unknown: []
    };
    Object.keys(properties).forEach(function (key) {
      if (requiredKeys.indexOf(key) !== -1 && !properties[key]) {
        errors.missing.push(key);
      }

      if (allKeys.indexOf(key) === -1) {
        errors.unknown.push(key);
      }
    });

    if (properties.serviceName && !/^[a-zA-Z0-9 _-]+$/.test(properties.serviceName)) {
      errors.invalid.push({
        key: 'serviceName',
        value: properties.serviceName,
        allowed: 'a-z, A-Z, 0-9, _, -, <space>'
      });
    }

    var sampleRate = properties.transactionSampleRate;

    if (typeof sampleRate !== 'undefined' && (typeof sampleRate !== 'number' || isNaN(sampleRate) || sampleRate < 0 || sampleRate > 1)) {
      errors.invalid.push({
        key: 'transactionSampleRate',
        value: sampleRate,
        allowed: 'Number between 0 and 1'
      });
    }

    return errors;
  };

  _proto.getLocalConfig = function getLocalConfig() {
    var storage = sessionStorage;

    if (this.config.session) {
      storage = localStorage;
    }

    var config = storage.getItem(_constants__WEBPACK_IMPORTED_MODULE_2__.LOCAL_CONFIG_KEY);

    if (config) {
      return JSON.parse(config);
    }
  };

  _proto.setLocalConfig = function setLocalConfig(config, merge) {
    if (config) {
      if (merge) {
        var prevConfig = this.getLocalConfig();
        config = _extends({}, prevConfig, config);
      }

      var storage = sessionStorage;

      if (this.config.session) {
        storage = localStorage;
      }

      storage.setItem(_constants__WEBPACK_IMPORTED_MODULE_2__.LOCAL_CONFIG_KEY, JSON.stringify(config));
    }
  };

  _proto.dispatchEvent = function dispatchEvent(name, args) {
    this.events.send(name, args);
  };

  _proto.observeEvent = function observeEvent(name, fn) {
    return this.events.observe(name, fn);
  };

  return Config;
}();

/* harmony default export */ __webpack_exports__["default"] = (Config);

/***/ }),

/***/ "../rum-core/dist/es/common/constants.js":
/*!***********************************************!*\
  !*** ../rum-core/dist/es/common/constants.js ***!
  \***********************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "SCHEDULE": function() { return /* binding */ SCHEDULE; },
/* harmony export */   "INVOKE": function() { return /* binding */ INVOKE; },
/* harmony export */   "ADD_EVENT_LISTENER_STR": function() { return /* binding */ ADD_EVENT_LISTENER_STR; },
/* harmony export */   "REMOVE_EVENT_LISTENER_STR": function() { return /* binding */ REMOVE_EVENT_LISTENER_STR; },
/* harmony export */   "RESOURCE_INITIATOR_TYPES": function() { return /* binding */ RESOURCE_INITIATOR_TYPES; },
/* harmony export */   "REUSABILITY_THRESHOLD": function() { return /* binding */ REUSABILITY_THRESHOLD; },
/* harmony export */   "MAX_SPAN_DURATION": function() { return /* binding */ MAX_SPAN_DURATION; },
/* harmony export */   "PAGE_LOAD_DELAY": function() { return /* binding */ PAGE_LOAD_DELAY; },
/* harmony export */   "PAGE_LOAD": function() { return /* binding */ PAGE_LOAD; },
/* harmony export */   "ROUTE_CHANGE": function() { return /* binding */ ROUTE_CHANGE; },
/* harmony export */   "NAME_UNKNOWN": function() { return /* binding */ NAME_UNKNOWN; },
/* harmony export */   "TYPE_CUSTOM": function() { return /* binding */ TYPE_CUSTOM; },
/* harmony export */   "USER_TIMING_THRESHOLD": function() { return /* binding */ USER_TIMING_THRESHOLD; },
/* harmony export */   "TRANSACTION_START": function() { return /* binding */ TRANSACTION_START; },
/* harmony export */   "TRANSACTION_END": function() { return /* binding */ TRANSACTION_END; },
/* harmony export */   "CONFIG_CHANGE": function() { return /* binding */ CONFIG_CHANGE; },
/* harmony export */   "QUEUE_FLUSH": function() { return /* binding */ QUEUE_FLUSH; },
/* harmony export */   "QUEUE_ADD_TRANSACTION": function() { return /* binding */ QUEUE_ADD_TRANSACTION; },
/* harmony export */   "XMLHTTPREQUEST": function() { return /* binding */ XMLHTTPREQUEST; },
/* harmony export */   "FETCH": function() { return /* binding */ FETCH; },
/* harmony export */   "HISTORY": function() { return /* binding */ HISTORY; },
/* harmony export */   "EVENT_TARGET": function() { return /* binding */ EVENT_TARGET; },
/* harmony export */   "CLICK": function() { return /* binding */ CLICK; },
/* harmony export */   "ERROR": function() { return /* binding */ ERROR; },
/* harmony export */   "BEFORE_EVENT": function() { return /* binding */ BEFORE_EVENT; },
/* harmony export */   "AFTER_EVENT": function() { return /* binding */ AFTER_EVENT; },
/* harmony export */   "LOCAL_CONFIG_KEY": function() { return /* binding */ LOCAL_CONFIG_KEY; },
/* harmony export */   "HTTP_REQUEST_TYPE": function() { return /* binding */ HTTP_REQUEST_TYPE; },
/* harmony export */   "LONG_TASK": function() { return /* binding */ LONG_TASK; },
/* harmony export */   "PAINT": function() { return /* binding */ PAINT; },
/* harmony export */   "MEASURE": function() { return /* binding */ MEASURE; },
/* harmony export */   "NAVIGATION": function() { return /* binding */ NAVIGATION; },
/* harmony export */   "RESOURCE": function() { return /* binding */ RESOURCE; },
/* harmony export */   "FIRST_CONTENTFUL_PAINT": function() { return /* binding */ FIRST_CONTENTFUL_PAINT; },
/* harmony export */   "LARGEST_CONTENTFUL_PAINT": function() { return /* binding */ LARGEST_CONTENTFUL_PAINT; },
/* harmony export */   "KEYWORD_LIMIT": function() { return /* binding */ KEYWORD_LIMIT; },
/* harmony export */   "TEMPORARY_TYPE": function() { return /* binding */ TEMPORARY_TYPE; },
/* harmony export */   "USER_INTERACTION": function() { return /* binding */ USER_INTERACTION; },
/* harmony export */   "TRANSACTION_TYPE_ORDER": function() { return /* binding */ TRANSACTION_TYPE_ORDER; },
/* harmony export */   "ERRORS": function() { return /* binding */ ERRORS; },
/* harmony export */   "TRANSACTIONS": function() { return /* binding */ TRANSACTIONS; },
/* harmony export */   "CONFIG_SERVICE": function() { return /* binding */ CONFIG_SERVICE; },
/* harmony export */   "LOGGING_SERVICE": function() { return /* binding */ LOGGING_SERVICE; },
/* harmony export */   "TRANSACTION_SERVICE": function() { return /* binding */ TRANSACTION_SERVICE; },
/* harmony export */   "APM_SERVER": function() { return /* binding */ APM_SERVER; },
/* harmony export */   "PERFORMANCE_MONITORING": function() { return /* binding */ PERFORMANCE_MONITORING; },
/* harmony export */   "ERROR_LOGGING": function() { return /* binding */ ERROR_LOGGING; },
/* harmony export */   "TRUNCATED_TYPE": function() { return /* binding */ TRUNCATED_TYPE; },
/* harmony export */   "FIRST_INPUT": function() { return /* binding */ FIRST_INPUT; },
/* harmony export */   "LAYOUT_SHIFT": function() { return /* binding */ LAYOUT_SHIFT; },
/* harmony export */   "OUTCOME_SUCCESS": function() { return /* binding */ OUTCOME_SUCCESS; },
/* harmony export */   "OUTCOME_FAILURE": function() { return /* binding */ OUTCOME_FAILURE; },
/* harmony export */   "OUTCOME_UNKNOWN": function() { return /* binding */ OUTCOME_UNKNOWN; },
/* harmony export */   "SESSION_TIMEOUT": function() { return /* binding */ SESSION_TIMEOUT; },
/* harmony export */   "HTTP_REQUEST_TIMEOUT": function() { return /* binding */ HTTP_REQUEST_TIMEOUT; }
/* harmony export */ });
var SCHEDULE = 'schedule';
var INVOKE = 'invoke';
var ADD_EVENT_LISTENER_STR = 'addEventListener';
var REMOVE_EVENT_LISTENER_STR = 'removeEventListener';
var RESOURCE_INITIATOR_TYPES = ['link', 'css', 'script', 'img', 'xmlhttprequest', 'fetch', 'beacon', 'iframe'];
var REUSABILITY_THRESHOLD = 5000;
var MAX_SPAN_DURATION = 5 * 60 * 1000;
var PAGE_LOAD_DELAY = 1000;
var PAGE_LOAD = 'page-load';
var ROUTE_CHANGE = 'route-change';
var TYPE_CUSTOM = 'custom';
var USER_INTERACTION = 'user-interaction';
var HTTP_REQUEST_TYPE = 'http-request';
var TEMPORARY_TYPE = 'temporary';
var NAME_UNKNOWN = 'Unknown';
var TRANSACTION_TYPE_ORDER = [PAGE_LOAD, ROUTE_CHANGE, USER_INTERACTION, HTTP_REQUEST_TYPE, TYPE_CUSTOM, TEMPORARY_TYPE];
var OUTCOME_SUCCESS = 'success';
var OUTCOME_FAILURE = 'failure';
var OUTCOME_UNKNOWN = 'unknown';
var USER_TIMING_THRESHOLD = 60;
var TRANSACTION_START = 'transaction:start';
var TRANSACTION_END = 'transaction:end';
var CONFIG_CHANGE = 'config:change';
var QUEUE_FLUSH = 'queue:flush';
var QUEUE_ADD_TRANSACTION = 'queue:add_transaction';
var XMLHTTPREQUEST = 'xmlhttprequest';
var FETCH = 'fetch';
var HISTORY = 'history';
var EVENT_TARGET = 'eventtarget';
var CLICK = 'click';
var ERROR = 'error';
var BEFORE_EVENT = ':before';
var AFTER_EVENT = ':after';
var LOCAL_CONFIG_KEY = 'elastic_apm_config';
var LONG_TASK = 'longtask';
var PAINT = 'paint';
var MEASURE = 'measure';
var NAVIGATION = 'navigation';
var RESOURCE = 'resource';
var FIRST_CONTENTFUL_PAINT = 'first-contentful-paint';
var LARGEST_CONTENTFUL_PAINT = 'largest-contentful-paint';
var FIRST_INPUT = 'first-input';
var LAYOUT_SHIFT = 'layout-shift';
var ERRORS = 'errors';
var TRANSACTIONS = 'transactions';
var CONFIG_SERVICE = 'ConfigService';
var LOGGING_SERVICE = 'LoggingService';
var TRANSACTION_SERVICE = 'TransactionService';
var APM_SERVER = 'ApmServer';
var PERFORMANCE_MONITORING = 'PerformanceMonitoring';
var ERROR_LOGGING = 'ErrorLogging';
var TRUNCATED_TYPE = '.truncated';
var KEYWORD_LIMIT = 1024;
var SESSION_TIMEOUT = 30 * 60000;
var HTTP_REQUEST_TIMEOUT = 10000;


/***/ }),

/***/ "../rum-core/dist/es/common/context.js":
/*!*********************************************!*\
  !*** ../rum-core/dist/es/common/context.js ***!
  \*********************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "getPageContext": function() { return /* binding */ getPageContext; },
/* harmony export */   "addSpanContext": function() { return /* binding */ addSpanContext; },
/* harmony export */   "addTransactionContext": function() { return /* binding */ addTransactionContext; }
/* harmony export */ });
/* harmony import */ var _url__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./url */ "../rum-core/dist/es/common/url.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./utils */ "../rum-core/dist/es/common/utils.js");
var _excluded = ["tags"];

function _objectWithoutPropertiesLoose(source, excluded) {
  if (source == null) return {};
  var target = {};
  var sourceKeys = Object.keys(source);
  var key, i;

  for (i = 0; i < sourceKeys.length; i++) {
    key = sourceKeys[i];
    if (excluded.indexOf(key) >= 0) continue;
    target[key] = source[key];
  }

  return target;
}




var LEFT_SQUARE_BRACKET = 91;
var RIGHT_SQUARE_BRACKET = 93;
var EXTERNAL = 'external';
var RESOURCE = 'resource';
var HARD_NAVIGATION = 'hard-navigation';

function getPortNumber(port, protocol) {
  if (port === '') {
    port = protocol === 'http:' ? '80' : protocol === 'https:' ? '443' : '';
  }

  return port;
}

function getResponseContext(perfTimingEntry) {
  var transferSize = perfTimingEntry.transferSize,
      encodedBodySize = perfTimingEntry.encodedBodySize,
      decodedBodySize = perfTimingEntry.decodedBodySize,
      serverTiming = perfTimingEntry.serverTiming;
  var respContext = {
    transfer_size: transferSize,
    encoded_body_size: encodedBodySize,
    decoded_body_size: decodedBodySize
  };
  var serverTimingStr = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.getServerTimingInfo)(serverTiming);

  if (serverTimingStr) {
    respContext.headers = {
      'server-timing': serverTimingStr
    };
  }

  return respContext;
}

function getDestination(parsedUrl) {
  var port = parsedUrl.port,
      protocol = parsedUrl.protocol,
      hostname = parsedUrl.hostname;
  var portNumber = getPortNumber(port, protocol);
  var ipv6Hostname = hostname.charCodeAt(0) === LEFT_SQUARE_BRACKET && hostname.charCodeAt(hostname.length - 1) === RIGHT_SQUARE_BRACKET;
  var address = hostname;

  if (ipv6Hostname) {
    address = hostname.slice(1, -1);
  }

  return {
    service: {
      resource: hostname + ':' + portNumber,
      name: '',
      type: ''
    },
    address: address,
    port: Number(portNumber)
  };
}

function getResourceContext(data) {
  var entry = data.entry,
      url = data.url;
  var parsedUrl = new _url__WEBPACK_IMPORTED_MODULE_1__.Url(url);
  var destination = getDestination(parsedUrl);
  return {
    http: {
      url: url,
      response: getResponseContext(entry)
    },
    destination: destination
  };
}

function getExternalContext(data) {
  var url = data.url,
      method = data.method,
      target = data.target,
      response = data.response;
  var parsedUrl = new _url__WEBPACK_IMPORTED_MODULE_1__.Url(url);
  var destination = getDestination(parsedUrl);
  var context = {
    http: {
      method: method,
      url: parsedUrl.href
    },
    destination: destination
  };
  var statusCode;

  if (target && typeof target.status !== 'undefined') {
    statusCode = target.status;
  } else if (response) {
    statusCode = response.status;
  }

  context.http.status_code = statusCode;
  return context;
}

function getNavigationContext(data) {
  var url = data.url;
  var parsedUrl = new _url__WEBPACK_IMPORTED_MODULE_1__.Url(url);
  var destination = getDestination(parsedUrl);
  return {
    destination: destination
  };
}

function getPageContext() {
  return {
    page: {
      referer: document.referrer,
      url: location.href
    }
  };
}
function addSpanContext(span, data) {
  if (!data) {
    return;
  }

  var type = span.type;
  var context;

  switch (type) {
    case EXTERNAL:
      context = getExternalContext(data);
      break;

    case RESOURCE:
      context = getResourceContext(data);
      break;

    case HARD_NAVIGATION:
      context = getNavigationContext(data);
      break;
  }

  span.addContext(context);
}
function addTransactionContext(transaction, _temp) {
  var _ref = _temp === void 0 ? {} : _temp,
      tags = _ref.tags,
      configContext = _objectWithoutPropertiesLoose(_ref, _excluded);

  var pageContext = getPageContext();
  var responseContext = {};

  if (transaction.type === _constants__WEBPACK_IMPORTED_MODULE_2__.PAGE_LOAD && (0,_utils__WEBPACK_IMPORTED_MODULE_0__.isPerfTimelineSupported)()) {
    var entries = _utils__WEBPACK_IMPORTED_MODULE_0__.PERF.getEntriesByType(_constants__WEBPACK_IMPORTED_MODULE_2__.NAVIGATION);

    if (entries && entries.length > 0) {
      responseContext = {
        response: getResponseContext(entries[0])
      };
    }
  }

  transaction.addContext(pageContext, responseContext, configContext);
}

/***/ }),

/***/ "../rum-core/dist/es/common/event-handler.js":
/*!***************************************************!*\
  !*** ../rum-core/dist/es/common/event-handler.js ***!
  \***************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./constants */ "../rum-core/dist/es/common/constants.js");


var EventHandler = function () {
  function EventHandler() {
    this.observers = {};
  }

  var _proto = EventHandler.prototype;

  _proto.observe = function observe(name, fn) {
    var _this = this;

    if (typeof fn === 'function') {
      if (!this.observers[name]) {
        this.observers[name] = [];
      }

      this.observers[name].push(fn);
      return function () {
        var index = _this.observers[name].indexOf(fn);

        if (index > -1) {
          _this.observers[name].splice(index, 1);
        }
      };
    }
  };

  _proto.sendOnly = function sendOnly(name, args) {
    var obs = this.observers[name];

    if (obs) {
      obs.forEach(function (fn) {
        try {
          fn.apply(undefined, args);
        } catch (error) {
          console.log(error, error.stack);
        }
      });
    }
  };

  _proto.send = function send(name, args) {
    this.sendOnly(name + _constants__WEBPACK_IMPORTED_MODULE_0__.BEFORE_EVENT, args);
    this.sendOnly(name, args);
    this.sendOnly(name + _constants__WEBPACK_IMPORTED_MODULE_0__.AFTER_EVENT, args);
  };

  return EventHandler;
}();

/* harmony default export */ __webpack_exports__["default"] = (EventHandler);

/***/ }),

/***/ "../rum-core/dist/es/common/http/fetch.js":
/*!************************************************!*\
  !*** ../rum-core/dist/es/common/http/fetch.js ***!
  \************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "BYTE_LIMIT": function() { return /* binding */ BYTE_LIMIT; },
/* harmony export */   "shouldUseFetchWithKeepAlive": function() { return /* binding */ shouldUseFetchWithKeepAlive; },
/* harmony export */   "sendFetchRequest": function() { return /* binding */ sendFetchRequest; },
/* harmony export */   "isFetchSupported": function() { return /* binding */ isFetchSupported; }
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _response_status__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./response-status */ "../rum-core/dist/es/common/http/response-status.js");
function _extends() {
  _extends = Object.assign || function (target) {
    for (var i = 1; i < arguments.length; i++) {
      var source = arguments[i];

      for (var key in source) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
          target[key] = source[key];
        }
      }
    }

    return target;
  };

  return _extends.apply(this, arguments);
}



var BYTE_LIMIT = 60 * 1000;
function shouldUseFetchWithKeepAlive(method, payload) {
  if (!isFetchSupported()) {
    return false;
  }

  var isKeepAliveSupported = ('keepalive' in new Request(''));

  if (!isKeepAliveSupported) {
    return false;
  }

  var size = calculateSize(payload);
  return method === 'POST' && size < BYTE_LIMIT;
}
function sendFetchRequest(method, url, _ref) {
  var _ref$keepalive = _ref.keepalive,
      keepalive = _ref$keepalive === void 0 ? false : _ref$keepalive,
      _ref$timeout = _ref.timeout,
      timeout = _ref$timeout === void 0 ? _constants__WEBPACK_IMPORTED_MODULE_0__.HTTP_REQUEST_TIMEOUT : _ref$timeout,
      payload = _ref.payload,
      headers = _ref.headers,
      sendCredentials = _ref.sendCredentials;
  var timeoutConfig = {};

  if (typeof AbortController === 'function') {
    var controller = new AbortController();
    timeoutConfig.signal = controller.signal;
    setTimeout(function () {
      return controller.abort();
    }, timeout);
  }

  var fetchResponse;
  return window.fetch(url, _extends({
    body: payload,
    headers: headers,
    method: method,
    keepalive: keepalive,
    credentials: sendCredentials ? 'include' : 'omit'
  }, timeoutConfig)).then(function (response) {
    fetchResponse = response;
    return fetchResponse.text();
  }).then(function (responseText) {
    var bodyResponse = {
      url: url,
      status: fetchResponse.status,
      responseText: responseText
    };

    if (!(0,_response_status__WEBPACK_IMPORTED_MODULE_1__.isResponseSuccessful)(fetchResponse.status)) {
      throw bodyResponse;
    }

    return bodyResponse;
  });
}
function isFetchSupported() {
  return typeof window.fetch === 'function' && typeof window.Request === 'function';
}

function calculateSize(payload) {
  if (!payload) {
    return 0;
  }

  if (payload instanceof Blob) {
    return payload.size;
  }

  return new Blob([payload]).size;
}

/***/ }),

/***/ "../rum-core/dist/es/common/http/response-status.js":
/*!**********************************************************!*\
  !*** ../rum-core/dist/es/common/http/response-status.js ***!
  \**********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "isResponseSuccessful": function() { return /* binding */ isResponseSuccessful; }
/* harmony export */ });
function isResponseSuccessful(status) {
  if (status === 0 || status > 399 && status < 600) {
    return false;
  }

  return true;
}

/***/ }),

/***/ "../rum-core/dist/es/common/http/xhr.js":
/*!**********************************************!*\
  !*** ../rum-core/dist/es/common/http/xhr.js ***!
  \**********************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "sendXHR": function() { return /* binding */ sendXHR; }
/* harmony export */ });
/* harmony import */ var _patching_patch_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../patching/patch-utils */ "../rum-core/dist/es/common/patching/patch-utils.js");
/* harmony import */ var _response_status__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./response-status */ "../rum-core/dist/es/common/http/response-status.js");
/* harmony import */ var _polyfills__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../polyfills */ "../rum-core/dist/es/common/polyfills.js");



function sendXHR(method, url, _ref) {
  var _ref$timeout = _ref.timeout,
      timeout = _ref$timeout === void 0 ? HTTP_REQUEST_TIMEOUT : _ref$timeout,
      payload = _ref.payload,
      headers = _ref.headers,
      beforeSend = _ref.beforeSend,
      sendCredentials = _ref.sendCredentials;
  return new _polyfills__WEBPACK_IMPORTED_MODULE_0__.Promise(function (resolve, reject) {
    var xhr = new window.XMLHttpRequest();
    xhr[_patching_patch_utils__WEBPACK_IMPORTED_MODULE_1__.XHR_IGNORE] = true;
    xhr.open(method, url, true);
    xhr.timeout = timeout;
    xhr.withCredentials = sendCredentials;

    if (headers) {
      for (var header in headers) {
        if (headers.hasOwnProperty(header)) {
          xhr.setRequestHeader(header, headers[header]);
        }
      }
    }

    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        var status = xhr.status,
            responseText = xhr.responseText;

        if ((0,_response_status__WEBPACK_IMPORTED_MODULE_2__.isResponseSuccessful)(status)) {
          resolve(xhr);
        } else {
          reject({
            url: url,
            status: status,
            responseText: responseText
          });
        }
      }
    };

    xhr.onerror = function () {
      var status = xhr.status,
          responseText = xhr.responseText;
      reject({
        url: url,
        status: status,
        responseText: responseText
      });
    };

    var canSend = true;

    if (typeof beforeSend === 'function') {
      canSend = beforeSend({
        url: url,
        method: method,
        headers: headers,
        payload: payload,
        xhr: xhr
      });
    }

    if (canSend) {
      xhr.send(payload);
    } else {
      reject({
        url: url,
        status: 0,
        responseText: 'Request rejected by user configuration.'
      });
    }
  });
}

/***/ }),

/***/ "../rum-core/dist/es/common/instrument.js":
/*!************************************************!*\
  !*** ../rum-core/dist/es/common/instrument.js ***!
  \************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "getInstrumentationFlags": function() { return /* binding */ getInstrumentationFlags; }
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./constants */ "../rum-core/dist/es/common/constants.js");

function getInstrumentationFlags(instrument, disabledInstrumentations) {
  var _flags;

  var flags = (_flags = {}, _flags[_constants__WEBPACK_IMPORTED_MODULE_0__.XMLHTTPREQUEST] = false, _flags[_constants__WEBPACK_IMPORTED_MODULE_0__.FETCH] = false, _flags[_constants__WEBPACK_IMPORTED_MODULE_0__.HISTORY] = false, _flags[_constants__WEBPACK_IMPORTED_MODULE_0__.PAGE_LOAD] = false, _flags[_constants__WEBPACK_IMPORTED_MODULE_0__.ERROR] = false, _flags[_constants__WEBPACK_IMPORTED_MODULE_0__.EVENT_TARGET] = false, _flags[_constants__WEBPACK_IMPORTED_MODULE_0__.CLICK] = false, _flags);

  if (!instrument) {
    return flags;
  }

  Object.keys(flags).forEach(function (key) {
    if (disabledInstrumentations.indexOf(key) === -1) {
      flags[key] = true;
    }
  });
  return flags;
}

/***/ }),

/***/ "../rum-core/dist/es/common/logging-service.js":
/*!*****************************************************!*\
  !*** ../rum-core/dist/es/common/logging-service.js ***!
  \*****************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./utils */ "../rum-core/dist/es/common/utils.js");


var LoggingService = function () {
  function LoggingService(spec) {
    if (spec === void 0) {
      spec = {};
    }

    this.levels = ['trace', 'debug', 'info', 'warn', 'error'];
    this.level = spec.level || 'warn';
    this.prefix = spec.prefix || '';
    this.resetLogMethods();
  }

  var _proto = LoggingService.prototype;

  _proto.shouldLog = function shouldLog(level) {
    return this.levels.indexOf(level) >= this.levels.indexOf(this.level);
  };

  _proto.setLevel = function setLevel(level) {
    if (level === this.level) {
      return;
    }

    this.level = level;
    this.resetLogMethods();
  };

  _proto.resetLogMethods = function resetLogMethods() {
    var _this = this;

    this.levels.forEach(function (level) {
      _this[level] = _this.shouldLog(level) ? log : _utils__WEBPACK_IMPORTED_MODULE_0__.noop;

      function log() {
        var normalizedLevel = level;

        if (level === 'trace' || level === 'debug') {
          normalizedLevel = 'info';
        }

        var args = arguments;
        args[0] = this.prefix + args[0];

        if (console) {
          var realMethod = console[normalizedLevel] || console.log;

          if (typeof realMethod === 'function') {
            realMethod.apply(console, args);
          }
        }
      }
    });
  };

  return LoggingService;
}();

/* harmony default export */ __webpack_exports__["default"] = (LoggingService);

/***/ }),

/***/ "../rum-core/dist/es/common/ndjson.js":
/*!********************************************!*\
  !*** ../rum-core/dist/es/common/ndjson.js ***!
  \********************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
var NDJSON = function () {
  function NDJSON() {}

  NDJSON.stringify = function stringify(object) {
    return JSON.stringify(object) + '\n';
  };

  return NDJSON;
}();

/* harmony default export */ __webpack_exports__["default"] = (NDJSON);

/***/ }),

/***/ "../rum-core/dist/es/common/observers/page-clicks.js":
/*!***********************************************************!*\
  !*** ../rum-core/dist/es/common/observers/page-clicks.js ***!
  \***********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "observePageClicks": function() { return /* binding */ observePageClicks; }
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../constants */ "../rum-core/dist/es/common/constants.js");

function observePageClicks(transactionService) {
  var clickHandler = function clickHandler(event) {
    if (event.target instanceof Element) {
      createUserInteractionTransaction(transactionService, event.target);
    }
  };

  var eventName = 'click';
  var useCapture = true;
  window.addEventListener(eventName, clickHandler, useCapture);
  return function () {
    window.removeEventListener(eventName, clickHandler, useCapture);
  };
}

function createUserInteractionTransaction(transactionService, target) {
  var _getTransactionMetada = getTransactionMetadata(target),
      transactionName = _getTransactionMetada.transactionName,
      context = _getTransactionMetada.context;

  var tr = transactionService.startTransaction("Click - " + transactionName, _constants__WEBPACK_IMPORTED_MODULE_0__.USER_INTERACTION, {
    managed: true,
    canReuse: true,
    reuseThreshold: 300
  });

  if (tr && context) {
    tr.addContext(context);
  }
}

function getTransactionMetadata(target) {
  var metadata = {
    transactionName: null,
    context: null
  };
  var tagName = target.tagName.toLowerCase();
  var transactionName = tagName;

  if (!!target.dataset.transactionName) {
    transactionName = target.dataset.transactionName;
  } else {
    var name = target.getAttribute('name');

    if (!!name) {
      transactionName = tagName + "[\"" + name + "\"]";
    }
  }

  metadata.transactionName = transactionName;
  var classes = target.getAttribute('class');

  if (classes) {
    metadata.context = {
      custom: {
        classes: classes
      }
    };
  }

  return metadata;
}

/***/ }),

/***/ "../rum-core/dist/es/common/observers/page-visibility.js":
/*!***************************************************************!*\
  !*** ../rum-core/dist/es/common/observers/page-visibility.js ***!
  \***************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "observePageVisibility": function() { return /* binding */ observePageVisibility; }
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _state__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../../state */ "../rum-core/dist/es/state.js");
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../utils */ "../rum-core/dist/es/common/utils.js");



function observePageVisibility(configService, transactionService) {
  if (document.visibilityState === 'hidden') {
    _state__WEBPACK_IMPORTED_MODULE_0__.state.lastHiddenStart = 0;
  }

  var visibilityChangeHandler = function visibilityChangeHandler() {
    if (document.visibilityState === 'hidden') {
      onPageHidden(configService, transactionService);
    }
  };

  var pageHideHandler = function pageHideHandler() {
    return onPageHidden(configService, transactionService);
  };

  var useCapture = true;
  window.addEventListener('visibilitychange', visibilityChangeHandler, useCapture);
  window.addEventListener('pagehide', pageHideHandler, useCapture);
  return function () {
    window.removeEventListener('visibilitychange', visibilityChangeHandler, useCapture);
    window.removeEventListener('pagehide', pageHideHandler, useCapture);
  };
}

function onPageHidden(configService, transactionService) {
  var tr = transactionService.getCurrentTransaction();

  if (tr) {
    var unobserve = configService.observeEvent(_constants__WEBPACK_IMPORTED_MODULE_1__.QUEUE_ADD_TRANSACTION, function () {
      configService.dispatchEvent(_constants__WEBPACK_IMPORTED_MODULE_1__.QUEUE_FLUSH);
      _state__WEBPACK_IMPORTED_MODULE_0__.state.lastHiddenStart = (0,_utils__WEBPACK_IMPORTED_MODULE_2__.now)();
      unobserve();
    });
    tr.end();
  } else {
    configService.dispatchEvent(_constants__WEBPACK_IMPORTED_MODULE_1__.QUEUE_FLUSH);
    _state__WEBPACK_IMPORTED_MODULE_0__.state.lastHiddenStart = (0,_utils__WEBPACK_IMPORTED_MODULE_2__.now)();
  }
}

/***/ }),

/***/ "../rum-core/dist/es/common/patching/fetch-patch.js":
/*!**********************************************************!*\
  !*** ../rum-core/dist/es/common/patching/fetch-patch.js ***!
  \**********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "patchFetch": function() { return /* binding */ patchFetch; }
/* harmony export */ });
/* harmony import */ var _polyfills__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../polyfills */ "../rum-core/dist/es/common/polyfills.js");
/* harmony import */ var _patch_utils__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./patch-utils */ "../rum-core/dist/es/common/patching/patch-utils.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _http_fetch__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../http/fetch */ "../rum-core/dist/es/common/http/fetch.js");





function patchFetch(callback) {
  if (!(0,_http_fetch__WEBPACK_IMPORTED_MODULE_0__.isFetchSupported)()) {
    return;
  }

  function scheduleTask(task) {
    task.state = _constants__WEBPACK_IMPORTED_MODULE_1__.SCHEDULE;
    callback(_constants__WEBPACK_IMPORTED_MODULE_1__.SCHEDULE, task);
  }

  function invokeTask(task) {
    task.state = _constants__WEBPACK_IMPORTED_MODULE_1__.INVOKE;
    callback(_constants__WEBPACK_IMPORTED_MODULE_1__.INVOKE, task);
  }

  function handleResponseError(task, error) {
    task.data.aborted = isAbortError(error);
    task.data.error = error;
    invokeTask(task);
  }

  function readStream(stream, task) {
    var reader = stream.getReader();

    var read = function read() {
      reader.read().then(function (_ref) {
        var done = _ref.done;

        if (done) {
          invokeTask(task);
        } else {
          read();
        }
      }, function (error) {
        handleResponseError(task, error);
      });
    };

    read();
  }

  var nativeFetch = window.fetch;

  window.fetch = function (input, init) {
    var fetchSelf = this;
    var args = arguments;
    var request, url;

    if (typeof input === 'string') {
      request = new Request(input, init);
      url = input;
    } else if (input) {
      request = input;
      url = request.url;
    } else {
      return nativeFetch.apply(fetchSelf, args);
    }

    var task = {
      source: _constants__WEBPACK_IMPORTED_MODULE_1__.FETCH,
      state: '',
      type: 'macroTask',
      data: {
        target: request,
        method: request.method,
        url: url,
        aborted: false
      }
    };
    return new _polyfills__WEBPACK_IMPORTED_MODULE_2__.Promise(function (resolve, reject) {
      _patch_utils__WEBPACK_IMPORTED_MODULE_3__.globalState.fetchInProgress = true;
      scheduleTask(task);
      var promise;

      try {
        promise = nativeFetch.apply(fetchSelf, [request]);
      } catch (error) {
        reject(error);
        task.data.error = error;
        invokeTask(task);
        _patch_utils__WEBPACK_IMPORTED_MODULE_3__.globalState.fetchInProgress = false;
        return;
      }

      promise.then(function (response) {
        var clonedResponse = response.clone ? response.clone() : {};
        resolve(response);
        (0,_utils__WEBPACK_IMPORTED_MODULE_4__.scheduleMicroTask)(function () {
          task.data.response = response;
          var body = clonedResponse.body;

          if (body) {
            readStream(body, task);
          } else {
            invokeTask(task);
          }
        });
      }, function (error) {
        reject(error);
        (0,_utils__WEBPACK_IMPORTED_MODULE_4__.scheduleMicroTask)(function () {
          handleResponseError(task, error);
        });
      });
      _patch_utils__WEBPACK_IMPORTED_MODULE_3__.globalState.fetchInProgress = false;
    });
  };
}

function isAbortError(error) {
  return error && error.name === 'AbortError';
}

/***/ }),

/***/ "../rum-core/dist/es/common/patching/history-patch.js":
/*!************************************************************!*\
  !*** ../rum-core/dist/es/common/patching/history-patch.js ***!
  \************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "patchHistory": function() { return /* binding */ patchHistory; }
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../constants */ "../rum-core/dist/es/common/constants.js");

function patchHistory(callback) {
  if (!window.history) {
    return;
  }

  var nativePushState = history.pushState;

  if (typeof nativePushState === 'function') {
    history.pushState = function (state, title, url) {
      var task = {
        source: _constants__WEBPACK_IMPORTED_MODULE_0__.HISTORY,
        data: {
          state: state,
          title: title,
          url: url
        }
      };
      callback(_constants__WEBPACK_IMPORTED_MODULE_0__.INVOKE, task);
      nativePushState.apply(this, arguments);
    };
  }
}

/***/ }),

/***/ "../rum-core/dist/es/common/patching/index.js":
/*!****************************************************!*\
  !*** ../rum-core/dist/es/common/patching/index.js ***!
  \****************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "patchAll": function() { return /* binding */ patchAll; },
/* harmony export */   "patchEventHandler": function() { return /* binding */ patchEventHandler; }
/* harmony export */ });
/* harmony import */ var _xhr_patch__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./xhr-patch */ "../rum-core/dist/es/common/patching/xhr-patch.js");
/* harmony import */ var _fetch_patch__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./fetch-patch */ "../rum-core/dist/es/common/patching/fetch-patch.js");
/* harmony import */ var _history_patch__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./history-patch */ "../rum-core/dist/es/common/patching/history-patch.js");
/* harmony import */ var _event_handler__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../event-handler */ "../rum-core/dist/es/common/event-handler.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../constants */ "../rum-core/dist/es/common/constants.js");





var patchEventHandler = new _event_handler__WEBPACK_IMPORTED_MODULE_0__.default();
var alreadyPatched = false;

function patchAll() {
  if (!alreadyPatched) {
    alreadyPatched = true;
    (0,_xhr_patch__WEBPACK_IMPORTED_MODULE_1__.patchXMLHttpRequest)(function (event, task) {
      patchEventHandler.send(_constants__WEBPACK_IMPORTED_MODULE_2__.XMLHTTPREQUEST, [event, task]);
    });
    (0,_fetch_patch__WEBPACK_IMPORTED_MODULE_3__.patchFetch)(function (event, task) {
      patchEventHandler.send(_constants__WEBPACK_IMPORTED_MODULE_2__.FETCH, [event, task]);
    });
    (0,_history_patch__WEBPACK_IMPORTED_MODULE_4__.patchHistory)(function (event, task) {
      patchEventHandler.send(_constants__WEBPACK_IMPORTED_MODULE_2__.HISTORY, [event, task]);
    });
  }

  return patchEventHandler;
}



/***/ }),

/***/ "../rum-core/dist/es/common/patching/patch-utils.js":
/*!**********************************************************!*\
  !*** ../rum-core/dist/es/common/patching/patch-utils.js ***!
  \**********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "globalState": function() { return /* binding */ globalState; },
/* harmony export */   "apmSymbol": function() { return /* binding */ apmSymbol; },
/* harmony export */   "patchMethod": function() { return /* binding */ patchMethod; },
/* harmony export */   "XHR_IGNORE": function() { return /* binding */ XHR_IGNORE; },
/* harmony export */   "XHR_SYNC": function() { return /* binding */ XHR_SYNC; },
/* harmony export */   "XHR_URL": function() { return /* binding */ XHR_URL; },
/* harmony export */   "XHR_METHOD": function() { return /* binding */ XHR_METHOD; }
/* harmony export */ });
var globalState = {
  fetchInProgress: false
};
function apmSymbol(name) {
  return '__apm_symbol__' + name;
}

function isPropertyWritable(propertyDesc) {
  if (!propertyDesc) {
    return true;
  }

  if (propertyDesc.writable === false) {
    return false;
  }

  return !(typeof propertyDesc.get === 'function' && typeof propertyDesc.set === 'undefined');
}

function attachOriginToPatched(patched, original) {
  patched[apmSymbol('OriginalDelegate')] = original;
}

function patchMethod(target, name, patchFn) {
  var proto = target;

  while (proto && !proto.hasOwnProperty(name)) {
    proto = Object.getPrototypeOf(proto);
  }

  if (!proto && target[name]) {
    proto = target;
  }

  var delegateName = apmSymbol(name);
  var delegate;

  if (proto && !(delegate = proto[delegateName])) {
    delegate = proto[delegateName] = proto[name];
    var desc = proto && Object.getOwnPropertyDescriptor(proto, name);

    if (isPropertyWritable(desc)) {
      var patchDelegate = patchFn(delegate, delegateName, name);

      proto[name] = function () {
        return patchDelegate(this, arguments);
      };

      attachOriginToPatched(proto[name], delegate);
    }
  }

  return delegate;
}
var XHR_IGNORE = apmSymbol('xhrIgnore');
var XHR_SYNC = apmSymbol('xhrSync');
var XHR_URL = apmSymbol('xhrURL');
var XHR_METHOD = apmSymbol('xhrMethod');

/***/ }),

/***/ "../rum-core/dist/es/common/patching/xhr-patch.js":
/*!********************************************************!*\
  !*** ../rum-core/dist/es/common/patching/xhr-patch.js ***!
  \********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "patchXMLHttpRequest": function() { return /* binding */ patchXMLHttpRequest; }
/* harmony export */ });
/* harmony import */ var _patch_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./patch-utils */ "../rum-core/dist/es/common/patching/patch-utils.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../constants */ "../rum-core/dist/es/common/constants.js");


function patchXMLHttpRequest(callback) {
  var XMLHttpRequestPrototype = XMLHttpRequest.prototype;

  if (!XMLHttpRequestPrototype || !XMLHttpRequestPrototype[_constants__WEBPACK_IMPORTED_MODULE_0__.ADD_EVENT_LISTENER_STR]) {
    return;
  }

  var READY_STATE_CHANGE = 'readystatechange';
  var LOAD = 'load';
  var ERROR = 'error';
  var TIMEOUT = 'timeout';
  var ABORT = 'abort';

  function invokeTask(task, status) {
    if (task.state !== _constants__WEBPACK_IMPORTED_MODULE_0__.INVOKE) {
      task.state = _constants__WEBPACK_IMPORTED_MODULE_0__.INVOKE;
      task.data.status = status;
      callback(_constants__WEBPACK_IMPORTED_MODULE_0__.INVOKE, task);
    }
  }

  function scheduleTask(task) {
    if (task.state === _constants__WEBPACK_IMPORTED_MODULE_0__.SCHEDULE) {
      return;
    }

    task.state = _constants__WEBPACK_IMPORTED_MODULE_0__.SCHEDULE;
    callback(_constants__WEBPACK_IMPORTED_MODULE_0__.SCHEDULE, task);
    var target = task.data.target;

    function addListener(name) {
      target[_constants__WEBPACK_IMPORTED_MODULE_0__.ADD_EVENT_LISTENER_STR](name, function (_ref) {
        var type = _ref.type;

        if (type === READY_STATE_CHANGE) {
          if (target.readyState === 4 && target.status !== 0) {
            invokeTask(task, 'success');
          }
        } else {
          var status = type === LOAD ? 'success' : type;
          invokeTask(task, status);
        }
      });
    }

    addListener(READY_STATE_CHANGE);
    addListener(LOAD);
    addListener(TIMEOUT);
    addListener(ERROR);
    addListener(ABORT);
  }

  var openNative = (0,_patch_utils__WEBPACK_IMPORTED_MODULE_1__.patchMethod)(XMLHttpRequestPrototype, 'open', function () {
    return function (self, args) {
      if (!self[_patch_utils__WEBPACK_IMPORTED_MODULE_1__.XHR_IGNORE]) {
        self[_patch_utils__WEBPACK_IMPORTED_MODULE_1__.XHR_METHOD] = args[0];
        self[_patch_utils__WEBPACK_IMPORTED_MODULE_1__.XHR_URL] = args[1];
        self[_patch_utils__WEBPACK_IMPORTED_MODULE_1__.XHR_SYNC] = args[2] === false;
      }

      return openNative.apply(self, args);
    };
  });
  var sendNative = (0,_patch_utils__WEBPACK_IMPORTED_MODULE_1__.patchMethod)(XMLHttpRequestPrototype, 'send', function () {
    return function (self, args) {
      if (self[_patch_utils__WEBPACK_IMPORTED_MODULE_1__.XHR_IGNORE]) {
        return sendNative.apply(self, args);
      }

      var task = {
        source: _constants__WEBPACK_IMPORTED_MODULE_0__.XMLHTTPREQUEST,
        state: '',
        type: 'macroTask',
        data: {
          target: self,
          method: self[_patch_utils__WEBPACK_IMPORTED_MODULE_1__.XHR_METHOD],
          sync: self[_patch_utils__WEBPACK_IMPORTED_MODULE_1__.XHR_SYNC],
          url: self[_patch_utils__WEBPACK_IMPORTED_MODULE_1__.XHR_URL],
          status: ''
        }
      };

      try {
        scheduleTask(task);
        return sendNative.apply(self, args);
      } catch (e) {
        invokeTask(task, ERROR);
        throw e;
      }
    };
  });
}

/***/ }),

/***/ "../rum-core/dist/es/common/polyfills.js":
/*!***********************************************!*\
  !*** ../rum-core/dist/es/common/polyfills.js ***!
  \***********************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "Promise": function() { return /* binding */ Promise; }
/* harmony export */ });
/* harmony import */ var promise_polyfill__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! promise-polyfill */ "../../node_modules/promise-polyfill/src/index.js");
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./utils */ "../rum-core/dist/es/common/utils.js");


var local = {};

if (_utils__WEBPACK_IMPORTED_MODULE_1__.isBrowser) {
  local = window;
} else if (typeof self !== 'undefined') {
  local = self;
}

var Promise = 'Promise' in local ? local.Promise : promise_polyfill__WEBPACK_IMPORTED_MODULE_0__.default;


/***/ }),

/***/ "../rum-core/dist/es/common/queue.js":
/*!*******************************************!*\
  !*** ../rum-core/dist/es/common/queue.js ***!
  \*******************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
var Queue = function () {
  function Queue(onFlush, opts) {
    if (opts === void 0) {
      opts = {};
    }

    this.onFlush = onFlush;
    this.items = [];
    this.queueLimit = opts.queueLimit || -1;
    this.flushInterval = opts.flushInterval || 0;
    this.timeoutId = undefined;
  }

  var _proto = Queue.prototype;

  _proto._setTimer = function _setTimer() {
    var _this = this;

    this.timeoutId = setTimeout(function () {
      return _this.flush();
    }, this.flushInterval);
  };

  _proto._clear = function _clear() {
    if (typeof this.timeoutId !== 'undefined') {
      clearTimeout(this.timeoutId);
      this.timeoutId = undefined;
    }

    this.items = [];
  };

  _proto.flush = function flush() {
    this.onFlush(this.items);

    this._clear();
  };

  _proto.add = function add(item) {
    this.items.push(item);

    if (this.queueLimit !== -1 && this.items.length >= this.queueLimit) {
      this.flush();
    } else {
      if (typeof this.timeoutId === 'undefined') {
        this._setTimer();
      }
    }
  };

  return Queue;
}();

/* harmony default export */ __webpack_exports__["default"] = (Queue);

/***/ }),

/***/ "../rum-core/dist/es/common/service-factory.js":
/*!*****************************************************!*\
  !*** ../rum-core/dist/es/common/service-factory.js ***!
  \*****************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "serviceCreators": function() { return /* binding */ serviceCreators; },
/* harmony export */   "ServiceFactory": function() { return /* binding */ ServiceFactory; }
/* harmony export */ });
/* harmony import */ var _apm_server__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./apm-server */ "../rum-core/dist/es/common/apm-server.js");
/* harmony import */ var _config_service__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./config-service */ "../rum-core/dist/es/common/config-service.js");
/* harmony import */ var _logging_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./logging-service */ "../rum-core/dist/es/common/logging-service.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _state__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../state */ "../rum-core/dist/es/state.js");
var _serviceCreators;






var serviceCreators = (_serviceCreators = {}, _serviceCreators[_constants__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE] = function () {
  return new _config_service__WEBPACK_IMPORTED_MODULE_1__.default();
}, _serviceCreators[_constants__WEBPACK_IMPORTED_MODULE_0__.LOGGING_SERVICE] = function () {
  return new _logging_service__WEBPACK_IMPORTED_MODULE_2__.default({
    prefix: '[Elastic APM] '
  });
}, _serviceCreators[_constants__WEBPACK_IMPORTED_MODULE_0__.APM_SERVER] = function (factory) {
  var _factory$getService = factory.getService([_constants__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE, _constants__WEBPACK_IMPORTED_MODULE_0__.LOGGING_SERVICE]),
      configService = _factory$getService[0],
      loggingService = _factory$getService[1];

  return new _apm_server__WEBPACK_IMPORTED_MODULE_3__.default(configService, loggingService);
}, _serviceCreators);

var ServiceFactory = function () {
  function ServiceFactory() {
    this.instances = {};
    this.initialized = false;
  }

  var _proto = ServiceFactory.prototype;

  _proto.init = function init() {
    if (this.initialized) {
      return;
    }

    this.initialized = true;
    var configService = this.getService(_constants__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE);
    configService.init();

    var _this$getService = this.getService([_constants__WEBPACK_IMPORTED_MODULE_0__.LOGGING_SERVICE, _constants__WEBPACK_IMPORTED_MODULE_0__.APM_SERVER]),
        loggingService = _this$getService[0],
        apmServer = _this$getService[1];

    configService.events.observe(_constants__WEBPACK_IMPORTED_MODULE_0__.CONFIG_CHANGE, function () {
      var logLevel = configService.get('logLevel');
      loggingService.setLevel(logLevel);
    });
    apmServer.init();
  };

  _proto.getService = function getService(name) {
    var _this = this;

    if (typeof name === 'string') {
      if (!this.instances[name]) {
        if (typeof serviceCreators[name] === 'function') {
          this.instances[name] = serviceCreators[name](this);
        } else if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
          console.log('Cannot get service, No creator for: ' + name);
        }
      }

      return this.instances[name];
    } else if (Array.isArray(name)) {
      return name.map(function (n) {
        return _this.getService(n);
      });
    }
  };

  return ServiceFactory;
}();



/***/ }),

/***/ "../rum-core/dist/es/common/throttle.js":
/*!**********************************************!*\
  !*** ../rum-core/dist/es/common/throttle.js ***!
  \**********************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": function() { return /* binding */ throttle; }
/* harmony export */ });
function throttle(fn, onThrottle, opts) {
  var context = this;
  var limit = opts.limit;
  var interval = opts.interval;
  var counter = 0;
  var timeoutId;
  return function () {
    counter++;

    if (typeof timeoutId === 'undefined') {
      timeoutId = setTimeout(function () {
        counter = 0;
        timeoutId = undefined;
      }, interval);
    }

    if (counter > limit && typeof onThrottle === 'function') {
      return onThrottle.apply(context, arguments);
    } else {
      return fn.apply(context, arguments);
    }
  };
}

/***/ }),

/***/ "../rum-core/dist/es/common/truncate.js":
/*!**********************************************!*\
  !*** ../rum-core/dist/es/common/truncate.js ***!
  \**********************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "truncate": function() { return /* binding */ truncate; },
/* harmony export */   "truncateModel": function() { return /* binding */ truncateModel; },
/* harmony export */   "SPAN_MODEL": function() { return /* binding */ SPAN_MODEL; },
/* harmony export */   "TRANSACTION_MODEL": function() { return /* binding */ TRANSACTION_MODEL; },
/* harmony export */   "ERROR_MODEL": function() { return /* binding */ ERROR_MODEL; },
/* harmony export */   "METADATA_MODEL": function() { return /* binding */ METADATA_MODEL; },
/* harmony export */   "RESPONSE_MODEL": function() { return /* binding */ RESPONSE_MODEL; }
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./constants */ "../rum-core/dist/es/common/constants.js");

var METADATA_MODEL = {
  service: {
    name: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
    version: true,
    agent: {
      version: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true]
    },
    environment: true
  },
  labels: {
    '*': true
  }
};
var RESPONSE_MODEL = {
  '*': true,
  headers: {
    '*': true
  }
};
var DESTINATION_MODEL = {
  address: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT],
  service: {
    '*': [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true]
  }
};
var CONTEXT_MODEL = {
  user: {
    id: true,
    email: true,
    username: true
  },
  tags: {
    '*': true
  },
  http: {
    response: RESPONSE_MODEL
  },
  destination: DESTINATION_MODEL,
  response: RESPONSE_MODEL
};
var SPAN_MODEL = {
  name: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  type: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  id: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  trace_id: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  parent_id: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  transaction_id: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  subtype: true,
  action: true,
  context: CONTEXT_MODEL
};
var TRANSACTION_MODEL = {
  name: true,
  parent_id: true,
  type: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  id: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  trace_id: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  span_count: {
    started: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true]
  },
  context: CONTEXT_MODEL
};
var ERROR_MODEL = {
  id: [_constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT, true],
  trace_id: true,
  transaction_id: true,
  parent_id: true,
  culprit: true,
  exception: {
    type: true
  },
  transaction: {
    type: true
  },
  context: CONTEXT_MODEL
};

function truncate(value, limit, required, placeholder) {
  if (limit === void 0) {
    limit = _constants__WEBPACK_IMPORTED_MODULE_0__.KEYWORD_LIMIT;
  }

  if (required === void 0) {
    required = false;
  }

  if (placeholder === void 0) {
    placeholder = 'N/A';
  }

  if (required && isEmpty(value)) {
    value = placeholder;
  }

  if (typeof value === 'string') {
    return value.substring(0, limit);
  }

  return value;
}

function isEmpty(value) {
  return value == null || value === '' || typeof value === 'undefined';
}

function replaceValue(target, key, currModel) {
  var value = truncate(target[key], currModel[0], currModel[1]);

  if (isEmpty(value)) {
    delete target[key];
    return;
  }

  target[key] = value;
}

function truncateModel(model, target, childTarget) {
  if (model === void 0) {
    model = {};
  }

  if (childTarget === void 0) {
    childTarget = target;
  }

  var keys = Object.keys(model);
  var emptyArr = [];

  var _loop = function _loop(i) {
    var currKey = keys[i];
    var currModel = model[currKey] === true ? emptyArr : model[currKey];

    if (!Array.isArray(currModel)) {
      truncateModel(currModel, target, childTarget[currKey]);
    } else {
      if (currKey === '*') {
        Object.keys(childTarget).forEach(function (key) {
          return replaceValue(childTarget, key, currModel);
        });
      } else {
        replaceValue(childTarget, currKey, currModel);
      }
    }
  };

  for (var i = 0; i < keys.length; i++) {
    _loop(i);
  }

  return target;
}



/***/ }),

/***/ "../rum-core/dist/es/common/url.js":
/*!*****************************************!*\
  !*** ../rum-core/dist/es/common/url.js ***!
  \*****************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "Url": function() { return /* binding */ Url; },
/* harmony export */   "slugifyUrl": function() { return /* binding */ slugifyUrl; }
/* harmony export */ });
/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./utils */ "../rum-core/dist/es/common/utils.js");


function isDefaultPort(port, protocol) {
  switch (protocol) {
    case 'http:':
      return port === '80';

    case 'https:':
      return port === '443';
  }

  return true;
}

var RULES = [['#', 'hash'], ['?', 'query'], ['/', 'path'], ['@', 'auth', 1], [NaN, 'host', undefined, 1]];
var PROTOCOL_REGEX = /^([a-z][a-z0-9.+-]*:)?(\/\/)?([\S\s]*)/i;
var Url = function () {
  function Url(url) {
    var _this$extractProtocol = this.extractProtocol(url || ''),
        protocol = _this$extractProtocol.protocol,
        address = _this$extractProtocol.address,
        slashes = _this$extractProtocol.slashes;

    var relative = !protocol && !slashes;
    var location = this.getLocation();
    var instructions = RULES.slice();
    address = address.replace('\\', '/');

    if (!slashes) {
      instructions[2] = [NaN, 'path'];
    }

    var index;

    for (var i = 0; i < instructions.length; i++) {
      var instruction = instructions[i];
      var parse = instruction[0];
      var key = instruction[1];

      if (typeof parse === 'string') {
        index = address.indexOf(parse);

        if (~index) {
          var instLength = instruction[2];

          if (instLength) {
            var newIndex = address.lastIndexOf(parse);
            index = Math.max(index, newIndex);
            this[key] = address.slice(0, index);
            address = address.slice(index + instLength);
          } else {
            this[key] = address.slice(index);
            address = address.slice(0, index);
          }
        }
      } else {
        this[key] = address;
        address = '';
      }

      this[key] = this[key] || (relative && instruction[3] ? location[key] || '' : '');
      if (instruction[3]) this[key] = this[key].toLowerCase();
    }

    if (relative && this.path.charAt(0) !== '/') {
      this.path = '/' + this.path;
    }

    this.relative = relative;
    this.protocol = protocol || location.protocol;
    this.hostname = this.host;
    this.port = '';

    if (/:\d+$/.test(this.host)) {
      var value = this.host.split(':');
      var port = value.pop();
      var hostname = value.join(':');

      if (isDefaultPort(port, this.protocol)) {
        this.host = hostname;
      } else {
        this.port = port;
      }

      this.hostname = hostname;
    }

    this.origin = this.protocol && this.host && this.protocol !== 'file:' ? this.protocol + '//' + this.host : 'null';
    this.href = this.toString();
  }

  var _proto = Url.prototype;

  _proto.toString = function toString() {
    var result = this.protocol;
    result += '//';

    if (this.auth) {
      var REDACTED = '[REDACTED]';
      var userpass = this.auth.split(':');
      var username = userpass[0] ? REDACTED : '';
      var password = userpass[1] ? ':' + REDACTED : '';
      result += username + password + '@';
    }

    result += this.host;
    result += this.path;
    result += this.query;
    result += this.hash;
    return result;
  };

  _proto.getLocation = function getLocation() {
    var globalVar = {};

    if (_utils__WEBPACK_IMPORTED_MODULE_0__.isBrowser) {
      globalVar = window;
    }

    return globalVar.location;
  };

  _proto.extractProtocol = function extractProtocol(url) {
    var match = PROTOCOL_REGEX.exec(url);
    return {
      protocol: match[1] ? match[1].toLowerCase() : '',
      slashes: !!match[2],
      address: match[3]
    };
  };

  return Url;
}();
function slugifyUrl(urlStr, depth) {
  if (depth === void 0) {
    depth = 2;
  }

  var parsedUrl = new Url(urlStr);
  var query = parsedUrl.query,
      path = parsedUrl.path;
  var pathParts = path.substring(1).split('/');
  var redactString = ':id';
  var wildcard = '*';
  var specialCharsRegex = /\W|_/g;
  var digitsRegex = /[0-9]/g;
  var lowerCaseRegex = /[a-z]/g;
  var upperCaseRegex = /[A-Z]/g;
  var redactedParts = [];
  var redactedBefore = false;

  for (var index = 0; index < pathParts.length; index++) {
    var part = pathParts[index];

    if (redactedBefore || index > depth - 1) {
      if (part) {
        redactedParts.push(wildcard);
      }

      break;
    }

    var numberOfSpecialChars = (part.match(specialCharsRegex) || []).length;

    if (numberOfSpecialChars >= 2) {
      redactedParts.push(redactString);
      redactedBefore = true;
      continue;
    }

    var numberOfDigits = (part.match(digitsRegex) || []).length;

    if (numberOfDigits > 3 || part.length > 3 && numberOfDigits / part.length >= 0.3) {
      redactedParts.push(redactString);
      redactedBefore = true;
      continue;
    }

    var numberofUpperCase = (part.match(upperCaseRegex) || []).length;
    var numberofLowerCase = (part.match(lowerCaseRegex) || []).length;
    var lowerCaseRate = numberofLowerCase / part.length;
    var upperCaseRate = numberofUpperCase / part.length;

    if (part.length > 5 && (upperCaseRate > 0.3 && upperCaseRate < 0.6 || lowerCaseRate > 0.3 && lowerCaseRate < 0.6)) {
      redactedParts.push(redactString);
      redactedBefore = true;
      continue;
    }

    part && redactedParts.push(part);
  }

  var redacted = '/' + (redactedParts.length >= 2 ? redactedParts.join('/') : redactedParts.join('')) + (query ? '?{query}' : '');
  return redacted;
}

/***/ }),

/***/ "../rum-core/dist/es/common/utils.js":
/*!*******************************************!*\
  !*** ../rum-core/dist/es/common/utils.js ***!
  \*******************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "extend": function() { return /* binding */ extend; },
/* harmony export */   "merge": function() { return /* binding */ merge; },
/* harmony export */   "isUndefined": function() { return /* binding */ isUndefined; },
/* harmony export */   "noop": function() { return /* binding */ noop; },
/* harmony export */   "baseExtend": function() { return /* binding */ baseExtend; },
/* harmony export */   "bytesToHex": function() { return /* binding */ bytesToHex; },
/* harmony export */   "isCORSSupported": function() { return /* binding */ isCORSSupported; },
/* harmony export */   "isObject": function() { return /* binding */ isObject; },
/* harmony export */   "isFunction": function() { return /* binding */ isFunction; },
/* harmony export */   "isPlatformSupported": function() { return /* binding */ isPlatformSupported; },
/* harmony export */   "isDtHeaderValid": function() { return /* binding */ isDtHeaderValid; },
/* harmony export */   "parseDtHeaderValue": function() { return /* binding */ parseDtHeaderValue; },
/* harmony export */   "getServerTimingInfo": function() { return /* binding */ getServerTimingInfo; },
/* harmony export */   "getDtHeaderValue": function() { return /* binding */ getDtHeaderValue; },
/* harmony export */   "getTSHeaderValue": function() { return /* binding */ getTSHeaderValue; },
/* harmony export */   "getCurrentScript": function() { return /* binding */ getCurrentScript; },
/* harmony export */   "getElasticScript": function() { return /* binding */ getElasticScript; },
/* harmony export */   "getTimeOrigin": function() { return /* binding */ getTimeOrigin; },
/* harmony export */   "generateRandomId": function() { return /* binding */ generateRandomId; },
/* harmony export */   "getEarliestSpan": function() { return /* binding */ getEarliestSpan; },
/* harmony export */   "getLatestNonXHRSpan": function() { return /* binding */ getLatestNonXHRSpan; },
/* harmony export */   "getLatestXHRSpan": function() { return /* binding */ getLatestXHRSpan; },
/* harmony export */   "getDuration": function() { return /* binding */ getDuration; },
/* harmony export */   "getTime": function() { return /* binding */ getTime; },
/* harmony export */   "now": function() { return /* binding */ now; },
/* harmony export */   "rng": function() { return /* binding */ rng; },
/* harmony export */   "checkSameOrigin": function() { return /* binding */ checkSameOrigin; },
/* harmony export */   "scheduleMacroTask": function() { return /* binding */ scheduleMacroTask; },
/* harmony export */   "scheduleMicroTask": function() { return /* binding */ scheduleMicroTask; },
/* harmony export */   "setLabel": function() { return /* binding */ setLabel; },
/* harmony export */   "setRequestHeader": function() { return /* binding */ setRequestHeader; },
/* harmony export */   "stripQueryStringFromUrl": function() { return /* binding */ stripQueryStringFromUrl; },
/* harmony export */   "find": function() { return /* binding */ find; },
/* harmony export */   "removeInvalidChars": function() { return /* binding */ removeInvalidChars; },
/* harmony export */   "PERF": function() { return /* binding */ PERF; },
/* harmony export */   "isPerfTimelineSupported": function() { return /* binding */ isPerfTimelineSupported; },
/* harmony export */   "isBrowser": function() { return /* binding */ isBrowser; },
/* harmony export */   "isPerfTypeSupported": function() { return /* binding */ isPerfTypeSupported; },
/* harmony export */   "isBeaconInspectionEnabled": function() { return /* binding */ isBeaconInspectionEnabled; }
/* harmony export */ });
/* harmony import */ var _polyfills__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./polyfills */ "../rum-core/dist/es/common/polyfills.js");

var slice = [].slice;
var isBrowser = typeof window !== 'undefined';
var PERF = isBrowser && typeof performance !== 'undefined' ? performance : {};

function isCORSSupported() {
  var xhr = new window.XMLHttpRequest();
  return 'withCredentials' in xhr;
}

var byteToHex = [];

for (var i = 0; i < 256; ++i) {
  byteToHex[i] = (i + 0x100).toString(16).substr(1);
}

function bytesToHex(buffer) {
  var hexOctets = [];

  for (var _i = 0; _i < buffer.length; _i++) {
    hexOctets.push(byteToHex[buffer[_i]]);
  }

  return hexOctets.join('');
}

var destination = new Uint8Array(16);

function rng() {
  if (typeof crypto != 'undefined' && typeof crypto.getRandomValues == 'function') {
    return crypto.getRandomValues(destination);
  } else if (typeof msCrypto != 'undefined' && typeof msCrypto.getRandomValues == 'function') {
    return msCrypto.getRandomValues(destination);
  }

  return destination;
}

function generateRandomId(length) {
  var id = bytesToHex(rng());
  return id.substr(0, length);
}

function getDtHeaderValue(span) {
  var dtVersion = '00';
  var dtUnSampledFlags = '00';
  var dtSampledFlags = '01';

  if (span && span.traceId && span.id && span.parentId) {
    var flags = span.sampled ? dtSampledFlags : dtUnSampledFlags;
    var id = span.sampled ? span.id : span.parentId;
    return dtVersion + '-' + span.traceId + '-' + id + '-' + flags;
  }
}

function parseDtHeaderValue(value) {
  var parsed = /^([\da-f]{2})-([\da-f]{32})-([\da-f]{16})-([\da-f]{2})$/.exec(value);

  if (parsed) {
    var flags = parsed[4];
    var sampled = flags !== '00';
    return {
      traceId: parsed[2],
      id: parsed[3],
      sampled: sampled
    };
  }
}

function isDtHeaderValid(header) {
  return /^[\da-f]{2}-[\da-f]{32}-[\da-f]{16}-[\da-f]{2}$/.test(header) && header.slice(3, 35) !== '00000000000000000000000000000000' && header.slice(36, 52) !== '0000000000000000';
}

function getTSHeaderValue(_ref) {
  var sampleRate = _ref.sampleRate;

  if (typeof sampleRate !== 'number' || String(sampleRate).length > 256) {
    return;
  }

  var NAMESPACE = 'es';
  var SEPARATOR = '=';
  return "" + NAMESPACE + SEPARATOR + "s:" + sampleRate;
}

function setRequestHeader(target, name, value) {
  if (typeof target.setRequestHeader === 'function') {
    target.setRequestHeader(name, value);
  } else if (target.headers && typeof target.headers.append === 'function') {
    target.headers.append(name, value);
  } else {
    target[name] = value;
  }
}

function checkSameOrigin(source, target) {
  var isSame = false;

  if (typeof target === 'string') {
    isSame = source === target;
  } else if (target && typeof target.test === 'function') {
    isSame = target.test(source);
  } else if (Array.isArray(target)) {
    target.forEach(function (t) {
      if (!isSame) {
        isSame = checkSameOrigin(source, t);
      }
    });
  }

  return isSame;
}

function isPlatformSupported() {
  return isBrowser && typeof Set === 'function' && typeof JSON.stringify === 'function' && PERF && typeof PERF.now === 'function' && isCORSSupported();
}

function setLabel(key, value, obj) {
  if (!obj || !key) return;
  var skey = removeInvalidChars(key);
  var valueType = typeof value;

  if (value != undefined && valueType !== 'boolean' && valueType !== 'number') {
    value = String(value);
  }

  obj[skey] = value;
  return obj;
}

function getServerTimingInfo(serverTimingEntries) {
  if (serverTimingEntries === void 0) {
    serverTimingEntries = [];
  }

  var serverTimingInfo = [];
  var entrySeparator = ', ';
  var valueSeparator = ';';

  for (var _i2 = 0; _i2 < serverTimingEntries.length; _i2++) {
    var _serverTimingEntries$ = serverTimingEntries[_i2],
        name = _serverTimingEntries$.name,
        duration = _serverTimingEntries$.duration,
        description = _serverTimingEntries$.description;
    var timingValue = name;

    if (description) {
      timingValue += valueSeparator + 'desc=' + description;
    }

    if (duration) {
      timingValue += valueSeparator + 'dur=' + duration;
    }

    serverTimingInfo.push(timingValue);
  }

  return serverTimingInfo.join(entrySeparator);
}

function getTimeOrigin() {
  return PERF.timing.fetchStart;
}

function stripQueryStringFromUrl(url) {
  return url && url.split('?')[0];
}

function isObject(value) {
  return value !== null && typeof value === 'object';
}

function isFunction(value) {
  return typeof value === 'function';
}

function baseExtend(dst, objs, deep) {
  for (var i = 0, ii = objs.length; i < ii; ++i) {
    var obj = objs[i];
    if (!isObject(obj) && !isFunction(obj)) continue;
    var keys = Object.keys(obj);

    for (var j = 0, jj = keys.length; j < jj; j++) {
      var key = keys[j];
      var src = obj[key];

      if (deep && isObject(src)) {
        if (!isObject(dst[key])) dst[key] = Array.isArray(src) ? [] : {};
        baseExtend(dst[key], [src], false);
      } else {
        dst[key] = src;
      }
    }
  }

  return dst;
}

function getElasticScript() {
  if (typeof document !== 'undefined') {
    var scripts = document.getElementsByTagName('script');

    for (var i = 0, l = scripts.length; i < l; i++) {
      var sc = scripts[i];

      if (sc.src.indexOf('elastic') > 0) {
        return sc;
      }
    }
  }
}

function getCurrentScript() {
  if (typeof document !== 'undefined') {
    var currentScript = document.currentScript;

    if (!currentScript) {
      return getElasticScript();
    }

    return currentScript;
  }
}

function extend(dst) {
  return baseExtend(dst, slice.call(arguments, 1), false);
}

function merge(dst) {
  return baseExtend(dst, slice.call(arguments, 1), true);
}

function isUndefined(obj) {
  return typeof obj === 'undefined';
}

function noop() {}

function find(array, predicate, thisArg) {
  if (array == null) {
    throw new TypeError('array is null or not defined');
  }

  var o = Object(array);
  var len = o.length >>> 0;

  if (typeof predicate !== 'function') {
    throw new TypeError('predicate must be a function');
  }

  var k = 0;

  while (k < len) {
    var kValue = o[k];

    if (predicate.call(thisArg, kValue, k, o)) {
      return kValue;
    }

    k++;
  }

  return undefined;
}

function removeInvalidChars(key) {
  return key.replace(/[.*"]/g, '_');
}

function getLatestSpan(spans, typeFilter) {
  var latestSpan = null;

  for (var _i3 = 0; _i3 < spans.length; _i3++) {
    var span = spans[_i3];

    if (typeFilter && typeFilter(span.type) && (!latestSpan || latestSpan._end < span._end)) {
      latestSpan = span;
    }
  }

  return latestSpan;
}

function getLatestNonXHRSpan(spans) {
  return getLatestSpan(spans, function (type) {
    return String(type).indexOf('external') === -1;
  });
}

function getLatestXHRSpan(spans) {
  return getLatestSpan(spans, function (type) {
    return String(type).indexOf('external') !== -1;
  });
}

function getEarliestSpan(spans) {
  var earliestSpan = spans[0];

  for (var _i4 = 1; _i4 < spans.length; _i4++) {
    var span = spans[_i4];

    if (earliestSpan._start > span._start) {
      earliestSpan = span;
    }
  }

  return earliestSpan;
}

function now() {
  return PERF.now();
}

function getTime(time) {
  return typeof time === 'number' && time >= 0 ? time : now();
}

function getDuration(start, end) {
  if (isUndefined(end) || isUndefined(start)) {
    return null;
  }

  return parseInt(end - start);
}

function scheduleMacroTask(callback) {
  setTimeout(callback, 0);
}

function scheduleMicroTask(callback) {
  _polyfills__WEBPACK_IMPORTED_MODULE_0__.Promise.resolve().then(callback);
}

function isPerfTimelineSupported() {
  return typeof PERF.getEntriesByType === 'function';
}

function isPerfTypeSupported(type) {
  return typeof PerformanceObserver !== 'undefined' && PerformanceObserver.supportedEntryTypes && PerformanceObserver.supportedEntryTypes.indexOf(type) >= 0;
}

function isBeaconInspectionEnabled() {
  var flagName = '_elastic_inspect_beacon_';

  if (sessionStorage.getItem(flagName) != null) {
    return true;
  }

  if (!window.URL || !window.URLSearchParams) {
    return false;
  }

  try {
    var parsedUrl = new URL(window.location.href);
    var isFlagSet = parsedUrl.searchParams.has(flagName);

    if (isFlagSet) {
      sessionStorage.setItem(flagName, true);
    }

    return isFlagSet;
  } catch (e) {}

  return false;
}



/***/ }),

/***/ "../rum-core/dist/es/error-logging/error-logging.js":
/*!**********************************************************!*\
  !*** ../rum-core/dist/es/error-logging/error-logging.js ***!
  \**********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _stack_trace__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./stack-trace */ "../rum-core/dist/es/error-logging/stack-trace.js");
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _common_context__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../common/context */ "../rum-core/dist/es/common/context.js");
/* harmony import */ var _common_truncate__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../common/truncate */ "../rum-core/dist/es/common/truncate.js");
/* harmony import */ var error_stack_parser__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! error-stack-parser */ "../../node_modules/error-stack-parser/error-stack-parser.js");
/* harmony import */ var error_stack_parser__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(error_stack_parser__WEBPACK_IMPORTED_MODULE_0__);
var _excluded = ["tags"];

function _objectWithoutPropertiesLoose(source, excluded) {
  if (source == null) return {};
  var target = {};
  var sourceKeys = Object.keys(source);
  var key, i;

  for (i = 0; i < sourceKeys.length; i++) {
    key = sourceKeys[i];
    if (excluded.indexOf(key) >= 0) continue;
    target[key] = source[key];
  }

  return target;
}






var IGNORE_KEYS = ['stack', 'message'];

function getErrorProperties(error) {
  var propertyFound = false;
  var properties = {};
  Object.keys(error).forEach(function (key) {
    if (IGNORE_KEYS.indexOf(key) >= 0) {
      return;
    }

    var val = error[key];

    if (val == null || typeof val === 'function') {
      return;
    }

    if (typeof val === 'object') {
      if (typeof val.toISOString !== 'function') return;
      val = val.toISOString();
    }

    properties[key] = val;
    propertyFound = true;
  });

  if (propertyFound) {
    return properties;
  }
}

var ErrorLogging = function () {
  function ErrorLogging(apmServer, configService, transactionService) {
    this._apmServer = apmServer;
    this._configService = configService;
    this._transactionService = transactionService;
  }

  var _proto = ErrorLogging.prototype;

  _proto.createErrorDataModel = function createErrorDataModel(errorEvent) {
    var frames = (0,_stack_trace__WEBPACK_IMPORTED_MODULE_1__.createStackTraces)((error_stack_parser__WEBPACK_IMPORTED_MODULE_0___default()), errorEvent);
    var filteredFrames = (0,_stack_trace__WEBPACK_IMPORTED_MODULE_1__.filterInvalidFrames)(frames);
    var culprit = '(inline script)';
    var lastFrame = filteredFrames[filteredFrames.length - 1];

    if (lastFrame && lastFrame.filename) {
      culprit = lastFrame.filename;
    }

    var message = errorEvent.message,
        error = errorEvent.error;
    var errorMessage = message;
    var errorType = '';
    var errorContext = {};

    if (error && typeof error === 'object') {
      errorMessage = errorMessage || error.message;
      errorType = error.name;
      var customProperties = getErrorProperties(error);

      if (customProperties) {
        errorContext.custom = customProperties;
      }
    }

    if (!errorType) {
      if (errorMessage && errorMessage.indexOf(':') > -1) {
        errorType = errorMessage.split(':')[0];
      }
    }

    var currentTransaction = this._transactionService.getCurrentTransaction();

    var transactionContext = currentTransaction ? currentTransaction.context : {};

    var _this$_configService$ = this._configService.get('context'),
        tags = _this$_configService$.tags,
        configContext = _objectWithoutPropertiesLoose(_this$_configService$, _excluded);

    var pageContext = (0,_common_context__WEBPACK_IMPORTED_MODULE_2__.getPageContext)();
    var context = (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.merge)({}, pageContext, transactionContext, configContext, errorContext);
    var errorObject = {
      id: (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.generateRandomId)(),
      culprit: culprit,
      exception: {
        message: errorMessage,
        stacktrace: filteredFrames,
        type: errorType
      },
      context: context
    };

    if (currentTransaction) {
      errorObject = (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.extend)(errorObject, {
        trace_id: currentTransaction.traceId,
        parent_id: currentTransaction.id,
        transaction_id: currentTransaction.id,
        transaction: {
          type: currentTransaction.type,
          sampled: currentTransaction.sampled
        }
      });
    }

    return (0,_common_truncate__WEBPACK_IMPORTED_MODULE_4__.truncateModel)(_common_truncate__WEBPACK_IMPORTED_MODULE_4__.ERROR_MODEL, errorObject);
  };

  _proto.logErrorEvent = function logErrorEvent(errorEvent) {
    if (typeof errorEvent === 'undefined') {
      return;
    }

    var errorObject = this.createErrorDataModel(errorEvent);

    if (typeof errorObject.exception.message === 'undefined') {
      return;
    }

    this._apmServer.addError(errorObject);
  };

  _proto.registerListeners = function registerListeners() {
    var _this = this;

    window.addEventListener('error', function (errorEvent) {
      return _this.logErrorEvent(errorEvent);
    });
    window.addEventListener('unhandledrejection', function (promiseRejectionEvent) {
      return _this.logPromiseEvent(promiseRejectionEvent);
    });
  };

  _proto.logPromiseEvent = function logPromiseEvent(promiseRejectionEvent) {
    var prefix = 'Unhandled promise rejection: ';
    var reason = promiseRejectionEvent.reason;

    if (reason == null) {
      reason = '<no reason specified>';
    }

    var errorEvent;

    if (typeof reason.message === 'string') {
      var name = reason.name ? reason.name + ': ' : '';
      errorEvent = {
        error: reason,
        message: prefix + name + reason.message
      };
    } else {
      reason = typeof reason === 'object' ? '<object>' : typeof reason === 'function' ? '<function>' : reason;
      errorEvent = {
        message: prefix + reason
      };
    }

    this.logErrorEvent(errorEvent);
  };

  _proto.logError = function logError(messageOrError) {
    var errorEvent = {};

    if (typeof messageOrError === 'string') {
      errorEvent.message = messageOrError;
    } else {
      errorEvent.error = messageOrError;
    }

    return this.logErrorEvent(errorEvent);
  };

  return ErrorLogging;
}();

/* harmony default export */ __webpack_exports__["default"] = (ErrorLogging);

/***/ }),

/***/ "../rum-core/dist/es/error-logging/index.js":
/*!**************************************************!*\
  !*** ../rum-core/dist/es/error-logging/index.js ***!
  \**************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "registerServices": function() { return /* binding */ registerServices; }
/* harmony export */ });
/* harmony import */ var _error_logging__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./error-logging */ "../rum-core/dist/es/error-logging/error-logging.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _common_service_factory__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../common/service-factory */ "../rum-core/dist/es/common/service-factory.js");




function registerServices() {
  _common_service_factory__WEBPACK_IMPORTED_MODULE_0__.serviceCreators[_common_constants__WEBPACK_IMPORTED_MODULE_1__.ERROR_LOGGING] = function (serviceFactory) {
    var _serviceFactory$getSe = serviceFactory.getService([_common_constants__WEBPACK_IMPORTED_MODULE_1__.APM_SERVER, _common_constants__WEBPACK_IMPORTED_MODULE_1__.CONFIG_SERVICE, _common_constants__WEBPACK_IMPORTED_MODULE_1__.TRANSACTION_SERVICE]),
        apmServer = _serviceFactory$getSe[0],
        configService = _serviceFactory$getSe[1],
        transactionService = _serviceFactory$getSe[2];

    return new _error_logging__WEBPACK_IMPORTED_MODULE_2__.default(apmServer, configService, transactionService);
  };
}



/***/ }),

/***/ "../rum-core/dist/es/error-logging/stack-trace.js":
/*!********************************************************!*\
  !*** ../rum-core/dist/es/error-logging/stack-trace.js ***!
  \********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "createStackTraces": function() { return /* binding */ createStackTraces; },
/* harmony export */   "filterInvalidFrames": function() { return /* binding */ filterInvalidFrames; }
/* harmony export */ });
function filePathToFileName(fileUrl) {
  var origin = window.location.origin || window.location.protocol + '//' + window.location.hostname + (window.location.port ? ':' + window.location.port : '');

  if (fileUrl.indexOf(origin) > -1) {
    fileUrl = fileUrl.replace(origin + '/', '');
  }

  return fileUrl;
}

function cleanFilePath(filePath) {
  if (filePath === void 0) {
    filePath = '';
  }

  if (filePath === '<anonymous>') {
    filePath = '';
  }

  return filePath;
}

function isFileInline(fileUrl) {
  if (fileUrl) {
    return window.location.href.indexOf(fileUrl) === 0;
  }

  return false;
}

function normalizeStackFrames(stackFrames) {
  return stackFrames.map(function (frame) {
    if (frame.functionName) {
      frame.functionName = normalizeFunctionName(frame.functionName);
    }

    return frame;
  });
}

function normalizeFunctionName(fnName) {
  var parts = fnName.split('/');

  if (parts.length > 1) {
    fnName = ['Object', parts[parts.length - 1]].join('.');
  } else {
    fnName = parts[0];
  }

  fnName = fnName.replace(/.<$/gi, '.<anonymous>');
  fnName = fnName.replace(/^Anonymous function$/, '<anonymous>');
  parts = fnName.split('.');

  if (parts.length > 1) {
    fnName = parts[parts.length - 1];
  } else {
    fnName = parts[0];
  }

  return fnName;
}

function isValidStackTrace(stackTraces) {
  if (stackTraces.length === 0) {
    return false;
  }

  if (stackTraces.length === 1) {
    var stackTrace = stackTraces[0];
    return 'lineNumber' in stackTrace;
  }

  return true;
}

function createStackTraces(stackParser, errorEvent) {
  var error = errorEvent.error,
      filename = errorEvent.filename,
      lineno = errorEvent.lineno,
      colno = errorEvent.colno;
  var stackTraces = [];

  if (error) {
    try {
      stackTraces = stackParser.parse(error);
    } catch (e) {}
  }

  if (!isValidStackTrace(stackTraces)) {
    stackTraces = [{
      fileName: filename,
      lineNumber: lineno,
      columnNumber: colno
    }];
  }

  var normalizedStackTraces = normalizeStackFrames(stackTraces);
  return normalizedStackTraces.map(function (stack) {
    var fileName = stack.fileName,
        lineNumber = stack.lineNumber,
        columnNumber = stack.columnNumber,
        _stack$functionName = stack.functionName,
        functionName = _stack$functionName === void 0 ? '<anonymous>' : _stack$functionName;

    if (!fileName && !lineNumber) {
      return {};
    }

    if (!columnNumber && !lineNumber) {
      return {};
    }

    var filePath = cleanFilePath(fileName);
    var cleanedFileName = filePathToFileName(filePath);

    if (isFileInline(filePath)) {
      cleanedFileName = '(inline script)';
    }

    return {
      abs_path: fileName,
      filename: cleanedFileName,
      function: functionName,
      lineno: lineNumber,
      colno: columnNumber
    };
  });
}
function filterInvalidFrames(frames) {
  return frames.filter(function (_ref) {
    var filename = _ref.filename,
        lineno = _ref.lineno;
    return typeof filename !== 'undefined' && typeof lineno !== 'undefined';
  });
}

/***/ }),

/***/ "../rum-core/dist/es/index.js":
/*!************************************!*\
  !*** ../rum-core/dist/es/index.js ***!
  \************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "createServiceFactory": function() { return /* binding */ createServiceFactory; },
/* harmony export */   "ServiceFactory": function() { return /* reexport safe */ _common_service_factory__WEBPACK_IMPORTED_MODULE_2__.ServiceFactory; },
/* harmony export */   "patchAll": function() { return /* reexport safe */ _common_patching__WEBPACK_IMPORTED_MODULE_3__.patchAll; },
/* harmony export */   "patchEventHandler": function() { return /* reexport safe */ _common_patching__WEBPACK_IMPORTED_MODULE_3__.patchEventHandler; },
/* harmony export */   "isPlatformSupported": function() { return /* reexport safe */ _common_utils__WEBPACK_IMPORTED_MODULE_4__.isPlatformSupported; },
/* harmony export */   "isBrowser": function() { return /* reexport safe */ _common_utils__WEBPACK_IMPORTED_MODULE_4__.isBrowser; },
/* harmony export */   "getInstrumentationFlags": function() { return /* reexport safe */ _common_instrument__WEBPACK_IMPORTED_MODULE_5__.getInstrumentationFlags; },
/* harmony export */   "createTracer": function() { return /* reexport safe */ _opentracing__WEBPACK_IMPORTED_MODULE_6__.createTracer; },
/* harmony export */   "scheduleMicroTask": function() { return /* reexport safe */ _common_utils__WEBPACK_IMPORTED_MODULE_4__.scheduleMicroTask; },
/* harmony export */   "scheduleMacroTask": function() { return /* reexport safe */ _common_utils__WEBPACK_IMPORTED_MODULE_4__.scheduleMacroTask; },
/* harmony export */   "afterFrame": function() { return /* reexport safe */ _common_after_frame__WEBPACK_IMPORTED_MODULE_7__.default; },
/* harmony export */   "ERROR": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.ERROR; },
/* harmony export */   "PAGE_LOAD_DELAY": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.PAGE_LOAD_DELAY; },
/* harmony export */   "PAGE_LOAD": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.PAGE_LOAD; },
/* harmony export */   "CONFIG_SERVICE": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.CONFIG_SERVICE; },
/* harmony export */   "LOGGING_SERVICE": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.LOGGING_SERVICE; },
/* harmony export */   "TRANSACTION_SERVICE": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.TRANSACTION_SERVICE; },
/* harmony export */   "APM_SERVER": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.APM_SERVER; },
/* harmony export */   "PERFORMANCE_MONITORING": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.PERFORMANCE_MONITORING; },
/* harmony export */   "ERROR_LOGGING": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.ERROR_LOGGING; },
/* harmony export */   "EVENT_TARGET": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.EVENT_TARGET; },
/* harmony export */   "CLICK": function() { return /* reexport safe */ _common_constants__WEBPACK_IMPORTED_MODULE_8__.CLICK; },
/* harmony export */   "bootstrap": function() { return /* reexport safe */ _bootstrap__WEBPACK_IMPORTED_MODULE_9__.bootstrap; },
/* harmony export */   "observePageVisibility": function() { return /* reexport safe */ _common_observers__WEBPACK_IMPORTED_MODULE_10__.observePageVisibility; },
/* harmony export */   "observePageClicks": function() { return /* reexport safe */ _common_observers__WEBPACK_IMPORTED_MODULE_11__.observePageClicks; }
/* harmony export */ });
/* harmony import */ var _error_logging__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./error-logging */ "../rum-core/dist/es/error-logging/index.js");
/* harmony import */ var _performance_monitoring__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./performance-monitoring */ "../rum-core/dist/es/performance-monitoring/index.js");
/* harmony import */ var _common_service_factory__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./common/service-factory */ "../rum-core/dist/es/common/service-factory.js");
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _common_patching__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./common/patching */ "../rum-core/dist/es/common/patching/index.js");
/* harmony import */ var _common_observers__WEBPACK_IMPORTED_MODULE_10__ = __webpack_require__(/*! ./common/observers */ "../rum-core/dist/es/common/observers/page-visibility.js");
/* harmony import */ var _common_observers__WEBPACK_IMPORTED_MODULE_11__ = __webpack_require__(/*! ./common/observers */ "../rum-core/dist/es/common/observers/page-clicks.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ./common/constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _common_instrument__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./common/instrument */ "../rum-core/dist/es/common/instrument.js");
/* harmony import */ var _common_after_frame__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./common/after-frame */ "../rum-core/dist/es/common/after-frame.js");
/* harmony import */ var _bootstrap__WEBPACK_IMPORTED_MODULE_9__ = __webpack_require__(/*! ./bootstrap */ "../rum-core/dist/es/bootstrap.js");
/* harmony import */ var _opentracing__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./opentracing */ "../rum-core/dist/es/opentracing/index.js");












function createServiceFactory() {
  (0,_performance_monitoring__WEBPACK_IMPORTED_MODULE_0__.registerServices)();
  (0,_error_logging__WEBPACK_IMPORTED_MODULE_1__.registerServices)();
  var serviceFactory = new _common_service_factory__WEBPACK_IMPORTED_MODULE_2__.ServiceFactory();
  return serviceFactory;
}



/***/ }),

/***/ "../rum-core/dist/es/opentracing/index.js":
/*!************************************************!*\
  !*** ../rum-core/dist/es/opentracing/index.js ***!
  \************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "Span": function() { return /* reexport safe */ _span__WEBPACK_IMPORTED_MODULE_2__.default; },
/* harmony export */   "Tracer": function() { return /* reexport safe */ _tracer__WEBPACK_IMPORTED_MODULE_1__.default; },
/* harmony export */   "createTracer": function() { return /* binding */ createTracer; }
/* harmony export */ });
/* harmony import */ var _tracer__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./tracer */ "../rum-core/dist/es/opentracing/tracer.js");
/* harmony import */ var _span__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./span */ "../rum-core/dist/es/opentracing/span.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");




function createTracer(serviceFactory) {
  var performanceMonitoring = serviceFactory.getService(_common_constants__WEBPACK_IMPORTED_MODULE_0__.PERFORMANCE_MONITORING);
  var transactionService = serviceFactory.getService(_common_constants__WEBPACK_IMPORTED_MODULE_0__.TRANSACTION_SERVICE);
  var errorLogging = serviceFactory.getService(_common_constants__WEBPACK_IMPORTED_MODULE_0__.ERROR_LOGGING);
  var loggingService = serviceFactory.getService(_common_constants__WEBPACK_IMPORTED_MODULE_0__.LOGGING_SERVICE);
  return new _tracer__WEBPACK_IMPORTED_MODULE_1__.default(performanceMonitoring, transactionService, loggingService, errorLogging);
}



/***/ }),

/***/ "../rum-core/dist/es/opentracing/span.js":
/*!***********************************************!*\
  !*** ../rum-core/dist/es/opentracing/span.js ***!
  \***********************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var opentracing_lib_span__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! opentracing/lib/span */ "../../node_modules/opentracing/lib/span.js");
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _performance_monitoring_transaction__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../performance-monitoring/transaction */ "../rum-core/dist/es/performance-monitoring/transaction.js");
function _inheritsLoose(subClass, superClass) {
  subClass.prototype = Object.create(superClass.prototype);
  subClass.prototype.constructor = subClass;

  _setPrototypeOf(subClass, superClass);
}

function _setPrototypeOf(o, p) {
  _setPrototypeOf = Object.setPrototypeOf || function _setPrototypeOf(o, p) {
    o.__proto__ = p;
    return o;
  };

  return _setPrototypeOf(o, p);
}





var Span = function (_otSpan) {
  _inheritsLoose(Span, _otSpan);

  function Span(tracer, span) {
    var _this;

    _this = _otSpan.call(this) || this;
    _this.__tracer = tracer;
    _this.span = span;
    _this.isTransaction = span instanceof _performance_monitoring_transaction__WEBPACK_IMPORTED_MODULE_1__.default;
    _this.spanContext = {
      id: span.id,
      traceId: span.traceId,
      sampled: span.sampled
    };
    return _this;
  }

  var _proto = Span.prototype;

  _proto._context = function _context() {
    return this.spanContext;
  };

  _proto._tracer = function _tracer() {
    return this.__tracer;
  };

  _proto._setOperationName = function _setOperationName(name) {
    this.span.name = name;
  };

  _proto._addTags = function _addTags(keyValuePairs) {
    var tags = (0,_common_utils__WEBPACK_IMPORTED_MODULE_2__.extend)({}, keyValuePairs);

    if (tags.type) {
      this.span.type = tags.type;
      delete tags.type;
    }

    if (this.isTransaction) {
      var userId = tags['user.id'];
      var username = tags['user.username'];
      var email = tags['user.email'];

      if (userId || username || email) {
        this.span.addContext({
          user: {
            id: userId,
            username: username,
            email: email
          }
        });
        delete tags['user.id'];
        delete tags['user.username'];
        delete tags['user.email'];
      }
    }

    this.span.addLabels(tags);
  };

  _proto._log = function _log(log, timestamp) {
    if (log.event === 'error') {
      if (log['error.object']) {
        this.__tracer.errorLogging.logError(log['error.object']);
      } else if (log.message) {
        this.__tracer.errorLogging.logError(log.message);
      }
    }
  };

  _proto._finish = function _finish(finishTime) {
    this.span.end();

    if (finishTime) {
      this.span._end = finishTime - (0,_common_utils__WEBPACK_IMPORTED_MODULE_2__.getTimeOrigin)();
    }
  };

  return Span;
}(opentracing_lib_span__WEBPACK_IMPORTED_MODULE_0__.Span);

/* harmony default export */ __webpack_exports__["default"] = (Span);

/***/ }),

/***/ "../rum-core/dist/es/opentracing/tracer.js":
/*!*************************************************!*\
  !*** ../rum-core/dist/es/opentracing/tracer.js ***!
  \*************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var opentracing_lib_tracer__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! opentracing/lib/tracer */ "../../node_modules/opentracing/lib/tracer.js");
/* harmony import */ var opentracing_lib_constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! opentracing/lib/constants */ "../../node_modules/opentracing/lib/constants.js");
/* harmony import */ var opentracing_lib_span__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! opentracing/lib/span */ "../../node_modules/opentracing/lib/span.js");
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _state__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../state */ "../rum-core/dist/es/state.js");
/* harmony import */ var _span__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ./span */ "../rum-core/dist/es/opentracing/span.js");
function _inheritsLoose(subClass, superClass) {
  subClass.prototype = Object.create(superClass.prototype);
  subClass.prototype.constructor = subClass;

  _setPrototypeOf(subClass, superClass);
}

function _setPrototypeOf(o, p) {
  _setPrototypeOf = Object.setPrototypeOf || function _setPrototypeOf(o, p) {
    o.__proto__ = p;
    return o;
  };

  return _setPrototypeOf(o, p);
}








var Tracer = function (_otTracer) {
  _inheritsLoose(Tracer, _otTracer);

  function Tracer(performanceMonitoring, transactionService, loggingService, errorLogging) {
    var _this;

    _this = _otTracer.call(this) || this;
    _this.performanceMonitoring = performanceMonitoring;
    _this.transactionService = transactionService;
    _this.loggingService = loggingService;
    _this.errorLogging = errorLogging;
    return _this;
  }

  var _proto = Tracer.prototype;

  _proto._startSpan = function _startSpan(name, options) {
    var spanOptions = {
      managed: true
    };

    if (options) {
      spanOptions.timestamp = options.startTime;

      if (options.childOf) {
        spanOptions.parentId = options.childOf.id;
      } else if (options.references && options.references.length > 0) {
        if (options.references.length > 1) {
          if (_state__WEBPACK_IMPORTED_MODULE_3__.__DEV__) {
            this.loggingService.debug('Elastic APM OpenTracing: Unsupported number of references, only the first childOf reference will be recorded.');
          }
        }

        var childRef = (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.find)(options.references, function (ref) {
          return ref.type() === opentracing_lib_constants__WEBPACK_IMPORTED_MODULE_1__.REFERENCE_CHILD_OF;
        });

        if (childRef) {
          spanOptions.parentId = childRef.referencedContext().id;
        }
      }
    }

    var span;
    var currentTransaction = this.transactionService.getCurrentTransaction();

    if (currentTransaction) {
      span = this.transactionService.startSpan(name, undefined, spanOptions);
    } else {
      span = this.transactionService.startTransaction(name, undefined, spanOptions);
    }

    if (!span) {
      return new opentracing_lib_span__WEBPACK_IMPORTED_MODULE_2__.Span();
    }

    if (spanOptions.timestamp) {
      span._start = spanOptions.timestamp - (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.getTimeOrigin)();
    }

    var otSpan = new _span__WEBPACK_IMPORTED_MODULE_5__.default(this, span);

    if (options && options.tags) {
      otSpan.addTags(options.tags);
    }

    return otSpan;
  };

  _proto._inject = function _inject(spanContext, format, carrier) {
    switch (format) {
      case opentracing_lib_constants__WEBPACK_IMPORTED_MODULE_1__.FORMAT_TEXT_MAP:
      case opentracing_lib_constants__WEBPACK_IMPORTED_MODULE_1__.FORMAT_HTTP_HEADERS:
        this.performanceMonitoring.injectDtHeader(spanContext, carrier);
        break;

      case opentracing_lib_constants__WEBPACK_IMPORTED_MODULE_1__.FORMAT_BINARY:
        if (_state__WEBPACK_IMPORTED_MODULE_3__.__DEV__) {
          this.loggingService.debug('Elastic APM OpenTracing: binary carrier format is not supported.');
        }

        break;
    }
  };

  _proto._extract = function _extract(format, carrier) {
    var ctx;

    switch (format) {
      case opentracing_lib_constants__WEBPACK_IMPORTED_MODULE_1__.FORMAT_TEXT_MAP:
      case opentracing_lib_constants__WEBPACK_IMPORTED_MODULE_1__.FORMAT_HTTP_HEADERS:
        ctx = this.performanceMonitoring.extractDtHeader(carrier);
        break;

      case opentracing_lib_constants__WEBPACK_IMPORTED_MODULE_1__.FORMAT_BINARY:
        if (_state__WEBPACK_IMPORTED_MODULE_3__.__DEV__) {
          this.loggingService.debug('Elastic APM OpenTracing: binary carrier format is not supported.');
        }

        break;
    }

    if (!ctx) {
      ctx = null;
    }

    return ctx;
  };

  return Tracer;
}(opentracing_lib_tracer__WEBPACK_IMPORTED_MODULE_0__.Tracer);

/* harmony default export */ __webpack_exports__["default"] = (Tracer);

/***/ }),

/***/ "../rum-core/dist/es/performance-monitoring/breakdown.js":
/*!***************************************************************!*\
  !*** ../rum-core/dist/es/performance-monitoring/breakdown.js ***!
  \***************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "captureBreakdown": function() { return /* binding */ captureBreakdown; }
/* harmony export */ });
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");


var pageLoadBreakdowns = [['domainLookupStart', 'domainLookupEnd', 'DNS'], ['connectStart', 'connectEnd', 'TCP'], ['requestStart', 'responseStart', 'Request'], ['responseStart', 'responseEnd', 'Response'], ['domLoading', 'domComplete', 'Processing'], ['loadEventStart', 'loadEventEnd', 'Load']];

function getValue(value) {
  return {
    value: value
  };
}

function calculateSelfTime(transaction) {
  var spans = transaction.spans,
      _start = transaction._start,
      _end = transaction._end;

  if (spans.length === 0) {
    return transaction.duration();
  }

  spans.sort(function (span1, span2) {
    return span1._start - span2._start;
  });
  var span = spans[0];
  var spanEnd = span._end;
  var spanStart = span._start;
  var lastContinuousEnd = spanEnd;
  var selfTime = spanStart - _start;

  for (var i = 1; i < spans.length; i++) {
    span = spans[i];
    spanStart = span._start;
    spanEnd = span._end;

    if (spanStart > lastContinuousEnd) {
      selfTime += spanStart - lastContinuousEnd;
      lastContinuousEnd = spanEnd;
    } else if (spanEnd > lastContinuousEnd) {
      lastContinuousEnd = spanEnd;
    }
  }

  if (lastContinuousEnd < _end) {
    selfTime += _end - lastContinuousEnd;
  }

  return selfTime;
}

function groupSpans(transaction) {
  var spanMap = {};
  var transactionSelfTime = calculateSelfTime(transaction);
  spanMap['app'] = {
    count: 1,
    duration: transactionSelfTime
  };
  var spans = transaction.spans;

  for (var i = 0; i < spans.length; i++) {
    var span = spans[i];
    var duration = span.duration();

    if (duration === 0 || duration == null) {
      continue;
    }

    var type = span.type,
        subtype = span.subtype;
    var key = type.replace(_common_constants__WEBPACK_IMPORTED_MODULE_0__.TRUNCATED_TYPE, '');

    if (subtype) {
      key += '.' + subtype;
    }

    if (!spanMap[key]) {
      spanMap[key] = {
        duration: 0,
        count: 0
      };
    }

    spanMap[key].count++;
    spanMap[key].duration += duration;
  }

  return spanMap;
}

function getSpanBreakdown(transactionDetails, _ref) {
  var details = _ref.details,
      _ref$count = _ref.count,
      count = _ref$count === void 0 ? 1 : _ref$count,
      duration = _ref.duration;
  return {
    transaction: transactionDetails,
    span: details,
    samples: {
      'span.self_time.count': getValue(count),
      'span.self_time.sum.us': getValue(duration)
    }
  };
}

function captureBreakdown(transaction, timings) {
  if (timings === void 0) {
    timings = _common_utils__WEBPACK_IMPORTED_MODULE_1__.PERF.timing;
  }

  var breakdowns = [];
  var trDuration = transaction.duration();
  var name = transaction.name,
      type = transaction.type,
      sampled = transaction.sampled;
  var transactionDetails = {
    name: name,
    type: type
  };
  breakdowns.push({
    transaction: transactionDetails,
    samples: {
      'transaction.duration.count': getValue(1),
      'transaction.duration.sum.us': getValue(trDuration),
      'transaction.breakdown.count': getValue(sampled ? 1 : 0)
    }
  });

  if (!sampled) {
    return breakdowns;
  }

  if (type === _common_constants__WEBPACK_IMPORTED_MODULE_0__.PAGE_LOAD && timings) {
    for (var i = 0; i < pageLoadBreakdowns.length; i++) {
      var current = pageLoadBreakdowns[i];
      var start = timings[current[0]];
      var end = timings[current[1]];
      var duration = (0,_common_utils__WEBPACK_IMPORTED_MODULE_1__.getDuration)(start, end);

      if (duration === 0 || duration == null) {
        continue;
      }

      breakdowns.push(getSpanBreakdown(transactionDetails, {
        details: {
          type: current[2]
        },
        duration: duration
      }));
    }
  } else {
    var spanMap = groupSpans(transaction);
    Object.keys(spanMap).forEach(function (key) {
      var _key$split = key.split('.'),
          type = _key$split[0],
          subtype = _key$split[1];

      var _spanMap$key = spanMap[key],
          duration = _spanMap$key.duration,
          count = _spanMap$key.count;
      breakdowns.push(getSpanBreakdown(transactionDetails, {
        details: {
          type: type,
          subtype: subtype
        },
        duration: duration,
        count: count
      }));
    });
  }

  return breakdowns;
}

/***/ }),

/***/ "../rum-core/dist/es/performance-monitoring/capture-navigation.js":
/*!************************************************************************!*\
  !*** ../rum-core/dist/es/performance-monitoring/capture-navigation.js ***!
  \************************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "getPageLoadMarks": function() { return /* binding */ getPageLoadMarks; },
/* harmony export */   "captureNavigation": function() { return /* binding */ captureNavigation; },
/* harmony export */   "createNavigationTimingSpans": function() { return /* binding */ createNavigationTimingSpans; },
/* harmony export */   "createResourceTimingSpans": function() { return /* binding */ createResourceTimingSpans; },
/* harmony export */   "createUserTimingSpans": function() { return /* binding */ createUserTimingSpans; },
/* harmony export */   "NAVIGATION_TIMING_MARKS": function() { return /* binding */ NAVIGATION_TIMING_MARKS; },
/* harmony export */   "COMPRESSED_NAV_TIMING_MARKS": function() { return /* binding */ COMPRESSED_NAV_TIMING_MARKS; }
/* harmony export */ });
/* harmony import */ var _span__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./span */ "../rum-core/dist/es/performance-monitoring/span.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _state__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../state */ "../rum-core/dist/es/state.js");




var eventPairs = [['domainLookupStart', 'domainLookupEnd', 'Domain lookup'], ['connectStart', 'connectEnd', 'Making a connection to the server'], ['requestStart', 'responseEnd', 'Requesting and receiving the document'], ['domLoading', 'domInteractive', 'Parsing the document, executing sync. scripts'], ['domContentLoadedEventStart', 'domContentLoadedEventEnd', 'Fire "DOMContentLoaded" event'], ['loadEventStart', 'loadEventEnd', 'Fire "load" event']];

function shouldCreateSpan(start, end, trStart, trEnd, baseTime) {
  if (baseTime === void 0) {
    baseTime = 0;
  }

  return typeof start === 'number' && typeof end === 'number' && start >= baseTime && end > start && start - baseTime >= trStart && end - baseTime <= trEnd && end - start < _common_constants__WEBPACK_IMPORTED_MODULE_0__.MAX_SPAN_DURATION && start - baseTime < _common_constants__WEBPACK_IMPORTED_MODULE_0__.MAX_SPAN_DURATION && end - baseTime < _common_constants__WEBPACK_IMPORTED_MODULE_0__.MAX_SPAN_DURATION;
}

function createNavigationTimingSpans(timings, baseTime, trStart, trEnd) {
  var spans = [];

  for (var i = 0; i < eventPairs.length; i++) {
    var start = timings[eventPairs[i][0]];
    var end = timings[eventPairs[i][1]];

    if (!shouldCreateSpan(start, end, trStart, trEnd, baseTime)) {
      continue;
    }

    var span = new _span__WEBPACK_IMPORTED_MODULE_1__.default(eventPairs[i][2], 'hard-navigation.browser-timing');
    var data = null;

    if (eventPairs[i][0] === 'requestStart') {
      span.pageResponse = true;
      data = {
        url: location.origin
      };
    }

    span._start = start - baseTime;
    span.end(end - baseTime, data);
    spans.push(span);
  }

  return spans;
}

function createResourceTimingSpan(resourceTimingEntry) {
  var name = resourceTimingEntry.name,
      initiatorType = resourceTimingEntry.initiatorType,
      startTime = resourceTimingEntry.startTime,
      responseEnd = resourceTimingEntry.responseEnd;
  var kind = 'resource';

  if (initiatorType) {
    kind += '.' + initiatorType;
  }

  var spanName = (0,_common_utils__WEBPACK_IMPORTED_MODULE_2__.stripQueryStringFromUrl)(name);
  var span = new _span__WEBPACK_IMPORTED_MODULE_1__.default(spanName, kind);
  span._start = startTime;
  span.end(responseEnd, {
    url: name,
    entry: resourceTimingEntry
  });
  return span;
}

function isCapturedByPatching(resourceStartTime, requestPatchTime) {
  return requestPatchTime != null && resourceStartTime > requestPatchTime;
}

function isIntakeAPIEndpoint(url) {
  return /intake\/v\d+\/rum\/events/.test(url);
}

function createResourceTimingSpans(entries, requestPatchTime, trStart, trEnd) {
  var spans = [];

  for (var i = 0; i < entries.length; i++) {
    var _entries$i = entries[i],
        initiatorType = _entries$i.initiatorType,
        name = _entries$i.name,
        startTime = _entries$i.startTime,
        responseEnd = _entries$i.responseEnd;

    if (_common_constants__WEBPACK_IMPORTED_MODULE_0__.RESOURCE_INITIATOR_TYPES.indexOf(initiatorType) === -1 || name == null) {
      continue;
    }

    if ((initiatorType === 'xmlhttprequest' || initiatorType === 'fetch') && (isIntakeAPIEndpoint(name) || isCapturedByPatching(startTime, requestPatchTime))) {
      continue;
    }

    if (shouldCreateSpan(startTime, responseEnd, trStart, trEnd)) {
      spans.push(createResourceTimingSpan(entries[i]));
    }
  }

  return spans;
}

function createUserTimingSpans(entries, trStart, trEnd) {
  var userTimingSpans = [];

  for (var i = 0; i < entries.length; i++) {
    var _entries$i2 = entries[i],
        name = _entries$i2.name,
        startTime = _entries$i2.startTime,
        duration = _entries$i2.duration;
    var end = startTime + duration;

    if (duration <= _common_constants__WEBPACK_IMPORTED_MODULE_0__.USER_TIMING_THRESHOLD || !shouldCreateSpan(startTime, end, trStart, trEnd)) {
      continue;
    }

    var kind = 'app';
    var span = new _span__WEBPACK_IMPORTED_MODULE_1__.default(name, kind);
    span._start = startTime;
    span.end(end);
    userTimingSpans.push(span);
  }

  return userTimingSpans;
}

var NAVIGATION_TIMING_MARKS = ['fetchStart', 'domainLookupStart', 'domainLookupEnd', 'connectStart', 'connectEnd', 'requestStart', 'responseStart', 'responseEnd', 'domLoading', 'domInteractive', 'domContentLoadedEventStart', 'domContentLoadedEventEnd', 'domComplete', 'loadEventStart', 'loadEventEnd'];
var COMPRESSED_NAV_TIMING_MARKS = ['fs', 'ls', 'le', 'cs', 'ce', 'qs', 'rs', 're', 'dl', 'di', 'ds', 'de', 'dc', 'es', 'ee'];

function getNavigationTimingMarks(timing) {
  var fetchStart = timing.fetchStart,
      navigationStart = timing.navigationStart,
      responseStart = timing.responseStart,
      responseEnd = timing.responseEnd;

  if (fetchStart >= navigationStart && responseStart >= fetchStart && responseEnd >= responseStart) {
    var marks = {};
    NAVIGATION_TIMING_MARKS.forEach(function (timingKey) {
      var m = timing[timingKey];

      if (m && m >= fetchStart) {
        marks[timingKey] = parseInt(m - fetchStart);
      }
    });
    return marks;
  }

  return null;
}

function getPageLoadMarks(timing) {
  var marks = getNavigationTimingMarks(timing);

  if (marks == null) {
    return null;
  }

  return {
    navigationTiming: marks,
    agent: {
      timeToFirstByte: marks.responseStart,
      domInteractive: marks.domInteractive,
      domComplete: marks.domComplete
    }
  };
}

function captureNavigation(transaction) {
  if (!transaction.captureTimings) {
    return;
  }

  var trEnd = transaction._end;

  if (transaction.type === _common_constants__WEBPACK_IMPORTED_MODULE_0__.PAGE_LOAD) {
    if (transaction.marks && transaction.marks.custom) {
      var customMarks = transaction.marks.custom;
      Object.keys(customMarks).forEach(function (key) {
        customMarks[key] += transaction._start;
      });
    }

    var trStart = 0;
    transaction._start = trStart;
    var timings = _common_utils__WEBPACK_IMPORTED_MODULE_2__.PERF.timing;
    createNavigationTimingSpans(timings, timings.fetchStart, trStart, trEnd).forEach(function (span) {
      span.traceId = transaction.traceId;
      span.sampled = transaction.sampled;

      if (span.pageResponse && transaction.options.pageLoadSpanId) {
        span.id = transaction.options.pageLoadSpanId;
      }

      transaction.spans.push(span);
    });
    transaction.addMarks(getPageLoadMarks(timings));
  }

  if ((0,_common_utils__WEBPACK_IMPORTED_MODULE_2__.isPerfTimelineSupported)()) {
    var _trStart = transaction._start;
    var resourceEntries = _common_utils__WEBPACK_IMPORTED_MODULE_2__.PERF.getEntriesByType(_common_constants__WEBPACK_IMPORTED_MODULE_0__.RESOURCE);
    createResourceTimingSpans(resourceEntries, _state__WEBPACK_IMPORTED_MODULE_3__.state.bootstrapTime, _trStart, trEnd).forEach(function (span) {
      return transaction.spans.push(span);
    });
    var userEntries = _common_utils__WEBPACK_IMPORTED_MODULE_2__.PERF.getEntriesByType(_common_constants__WEBPACK_IMPORTED_MODULE_0__.MEASURE);
    createUserTimingSpans(userEntries, _trStart, trEnd).forEach(function (span) {
      return transaction.spans.push(span);
    });
  }
}



/***/ }),

/***/ "../rum-core/dist/es/performance-monitoring/index.js":
/*!***********************************************************!*\
  !*** ../rum-core/dist/es/performance-monitoring/index.js ***!
  \***********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "registerServices": function() { return /* binding */ registerServices; }
/* harmony export */ });
/* harmony import */ var _performance_monitoring__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./performance-monitoring */ "../rum-core/dist/es/performance-monitoring/performance-monitoring.js");
/* harmony import */ var _transaction_service__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./transaction-service */ "../rum-core/dist/es/performance-monitoring/transaction-service.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _common_service_factory__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../common/service-factory */ "../rum-core/dist/es/common/service-factory.js");





function registerServices() {
  _common_service_factory__WEBPACK_IMPORTED_MODULE_0__.serviceCreators[_common_constants__WEBPACK_IMPORTED_MODULE_1__.TRANSACTION_SERVICE] = function (serviceFactory) {
    var _serviceFactory$getSe = serviceFactory.getService([_common_constants__WEBPACK_IMPORTED_MODULE_1__.LOGGING_SERVICE, _common_constants__WEBPACK_IMPORTED_MODULE_1__.CONFIG_SERVICE]),
        loggingService = _serviceFactory$getSe[0],
        configService = _serviceFactory$getSe[1];

    return new _transaction_service__WEBPACK_IMPORTED_MODULE_2__.default(loggingService, configService);
  };

  _common_service_factory__WEBPACK_IMPORTED_MODULE_0__.serviceCreators[_common_constants__WEBPACK_IMPORTED_MODULE_1__.PERFORMANCE_MONITORING] = function (serviceFactory) {
    var _serviceFactory$getSe2 = serviceFactory.getService([_common_constants__WEBPACK_IMPORTED_MODULE_1__.APM_SERVER, _common_constants__WEBPACK_IMPORTED_MODULE_1__.CONFIG_SERVICE, _common_constants__WEBPACK_IMPORTED_MODULE_1__.LOGGING_SERVICE, _common_constants__WEBPACK_IMPORTED_MODULE_1__.TRANSACTION_SERVICE]),
        apmServer = _serviceFactory$getSe2[0],
        configService = _serviceFactory$getSe2[1],
        loggingService = _serviceFactory$getSe2[2],
        transactionService = _serviceFactory$getSe2[3];

    return new _performance_monitoring__WEBPACK_IMPORTED_MODULE_3__.default(apmServer, configService, loggingService, transactionService);
  };
}



/***/ }),

/***/ "../rum-core/dist/es/performance-monitoring/metrics.js":
/*!*************************************************************!*\
  !*** ../rum-core/dist/es/performance-monitoring/metrics.js ***!
  \*************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "metrics": function() { return /* binding */ metrics; },
/* harmony export */   "createLongTaskSpans": function() { return /* binding */ createLongTaskSpans; },
/* harmony export */   "createFirstInputDelaySpan": function() { return /* binding */ createFirstInputDelaySpan; },
/* harmony export */   "createTotalBlockingTimeSpan": function() { return /* binding */ createTotalBlockingTimeSpan; },
/* harmony export */   "calculateTotalBlockingTime": function() { return /* binding */ calculateTotalBlockingTime; },
/* harmony export */   "calculateCumulativeLayoutShift": function() { return /* binding */ calculateCumulativeLayoutShift; },
/* harmony export */   "captureObserverEntries": function() { return /* binding */ captureObserverEntries; },
/* harmony export */   "PerfEntryRecorder": function() { return /* binding */ PerfEntryRecorder; }
/* harmony export */ });
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _span__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./span */ "../rum-core/dist/es/performance-monitoring/span.js");



var metrics = {
  fid: 0,
  fcp: 0,
  tbt: {
    start: Infinity,
    duration: 0
  },
  cls: {
    score: 0,
    firstEntryTime: Number.NEGATIVE_INFINITY,
    prevEntryTime: Number.NEGATIVE_INFINITY,
    currentSessionScore: 0
  },
  longtask: {
    count: 0,
    duration: 0,
    max: 0
  }
};
var LONG_TASK_THRESHOLD = 50;
function createLongTaskSpans(longtasks, agg) {
  var spans = [];

  for (var i = 0; i < longtasks.length; i++) {
    var _longtasks$i = longtasks[i],
        name = _longtasks$i.name,
        startTime = _longtasks$i.startTime,
        duration = _longtasks$i.duration,
        attribution = _longtasks$i.attribution;
    var end = startTime + duration;
    var span = new _span__WEBPACK_IMPORTED_MODULE_0__.default("Longtask(" + name + ")", _common_constants__WEBPACK_IMPORTED_MODULE_1__.LONG_TASK, {
      startTime: startTime
    });
    agg.count++;
    agg.duration += duration;
    agg.max = Math.max(duration, agg.max);

    if (attribution.length > 0) {
      var _attribution$ = attribution[0],
          _name = _attribution$.name,
          containerType = _attribution$.containerType,
          containerName = _attribution$.containerName,
          containerId = _attribution$.containerId;
      var customContext = {
        attribution: _name,
        type: containerType
      };

      if (containerName) {
        customContext.name = containerName;
      }

      if (containerId) {
        customContext.id = containerId;
      }

      span.addContext({
        custom: customContext
      });
    }

    span.end(end);
    spans.push(span);
  }

  return spans;
}
function createFirstInputDelaySpan(fidEntries) {
  var firstInput = fidEntries[0];

  if (firstInput) {
    var startTime = firstInput.startTime,
        processingStart = firstInput.processingStart;
    var span = new _span__WEBPACK_IMPORTED_MODULE_0__.default('First Input Delay', _common_constants__WEBPACK_IMPORTED_MODULE_1__.FIRST_INPUT, {
      startTime: startTime
    });
    span.end(processingStart);
    return span;
  }
}
function createTotalBlockingTimeSpan(tbtObject) {
  var start = tbtObject.start,
      duration = tbtObject.duration;
  var tbtSpan = new _span__WEBPACK_IMPORTED_MODULE_0__.default('Total Blocking Time', _common_constants__WEBPACK_IMPORTED_MODULE_1__.LONG_TASK, {
    startTime: start
  });
  tbtSpan.end(start + duration);
  return tbtSpan;
}
function calculateTotalBlockingTime(longtaskEntries) {
  longtaskEntries.forEach(function (entry) {
    var name = entry.name,
        startTime = entry.startTime,
        duration = entry.duration;

    if (startTime < metrics.fcp) {
      return;
    }

    if (name !== 'self' && name.indexOf('same-origin') === -1) {
      return;
    }

    metrics.tbt.start = Math.min(metrics.tbt.start, startTime);
    var blockingTime = duration - LONG_TASK_THRESHOLD;

    if (blockingTime > 0) {
      metrics.tbt.duration += blockingTime;
    }
  });
}
function calculateCumulativeLayoutShift(clsEntries) {
  clsEntries.forEach(function (entry) {
    if (!entry.hadRecentInput && entry.value) {
      var shouldCreateNewSession = entry.startTime - metrics.cls.firstEntryTime > 5000 || entry.startTime - metrics.cls.prevEntryTime > 1000;

      if (shouldCreateNewSession) {
        metrics.cls.firstEntryTime = entry.startTime;
        metrics.cls.currentSessionScore = 0;
      }

      metrics.cls.prevEntryTime = entry.startTime;
      metrics.cls.currentSessionScore += entry.value;
      metrics.cls.score = Math.max(metrics.cls.score, metrics.cls.currentSessionScore);
    }
  });
}
function captureObserverEntries(list, _ref) {
  var isHardNavigation = _ref.isHardNavigation,
      trStart = _ref.trStart;
  var longtaskEntries = list.getEntriesByType(_common_constants__WEBPACK_IMPORTED_MODULE_1__.LONG_TASK).filter(function (entry) {
    return entry.startTime >= trStart;
  });
  var longTaskSpans = createLongTaskSpans(longtaskEntries, metrics.longtask);
  var result = {
    spans: longTaskSpans,
    marks: {}
  };

  if (!isHardNavigation) {
    return result;
  }

  var lcpEntries = list.getEntriesByType(_common_constants__WEBPACK_IMPORTED_MODULE_1__.LARGEST_CONTENTFUL_PAINT);
  var lastLcpEntry = lcpEntries[lcpEntries.length - 1];

  if (lastLcpEntry) {
    var lcp = parseInt(lastLcpEntry.startTime);
    metrics.lcp = lcp;
    result.marks.largestContentfulPaint = lcp;
  }

  var timing = _common_utils__WEBPACK_IMPORTED_MODULE_2__.PERF.timing;
  var unloadDiff = timing.fetchStart - timing.navigationStart;
  var fcpEntry = list.getEntriesByName(_common_constants__WEBPACK_IMPORTED_MODULE_1__.FIRST_CONTENTFUL_PAINT)[0];

  if (fcpEntry) {
    var fcp = parseInt(unloadDiff >= 0 ? fcpEntry.startTime - unloadDiff : fcpEntry.startTime);
    metrics.fcp = fcp;
    result.marks.firstContentfulPaint = fcp;
  }

  var fidEntries = list.getEntriesByType(_common_constants__WEBPACK_IMPORTED_MODULE_1__.FIRST_INPUT);
  var fidSpan = createFirstInputDelaySpan(fidEntries);

  if (fidSpan) {
    metrics.fid = fidSpan.duration();
    result.spans.push(fidSpan);
  }

  calculateTotalBlockingTime(longtaskEntries);
  var clsEntries = list.getEntriesByType(_common_constants__WEBPACK_IMPORTED_MODULE_1__.LAYOUT_SHIFT);
  calculateCumulativeLayoutShift(clsEntries);
  return result;
}
var PerfEntryRecorder = function () {
  function PerfEntryRecorder(callback) {
    this.po = {
      observe: _common_utils__WEBPACK_IMPORTED_MODULE_2__.noop,
      disconnect: _common_utils__WEBPACK_IMPORTED_MODULE_2__.noop
    };

    if (window.PerformanceObserver) {
      this.po = new PerformanceObserver(callback);
    }
  }

  var _proto = PerfEntryRecorder.prototype;

  _proto.start = function start(type) {
    try {
      this.po.observe({
        type: type,
        buffered: true
      });
    } catch (_) {}
  };

  _proto.stop = function stop() {
    this.po.disconnect();
  };

  return PerfEntryRecorder;
}();

/***/ }),

/***/ "../rum-core/dist/es/performance-monitoring/performance-monitoring.js":
/*!****************************************************************************!*\
  !*** ../rum-core/dist/es/performance-monitoring/performance-monitoring.js ***!
  \****************************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "groupSmallContinuouslySimilarSpans": function() { return /* binding */ groupSmallContinuouslySimilarSpans; },
/* harmony export */   "adjustTransaction": function() { return /* binding */ adjustTransaction; },
/* harmony export */   "default": function() { return /* binding */ PerformanceMonitoring; }
/* harmony export */ });
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _common_url__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../common/url */ "../rum-core/dist/es/common/url.js");
/* harmony import */ var _common_patching__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../common/patching */ "../rum-core/dist/es/common/patching/index.js");
/* harmony import */ var _common_patching_patch_utils__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../common/patching/patch-utils */ "../rum-core/dist/es/common/patching/patch-utils.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _common_truncate__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ../common/truncate */ "../rum-core/dist/es/common/truncate.js");
/* harmony import */ var _state__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../state */ "../rum-core/dist/es/state.js");







var SIMILAR_SPAN_TO_TRANSACTION_RATIO = 0.05;
var TRANSACTION_DURATION_THRESHOLD = 60000;
function groupSmallContinuouslySimilarSpans(originalSpans, transDuration, threshold) {
  originalSpans.sort(function (spanA, spanB) {
    return spanA._start - spanB._start;
  });
  var spans = [];
  var lastCount = 1;
  originalSpans.forEach(function (span, index) {
    if (spans.length === 0) {
      spans.push(span);
    } else {
      var lastSpan = spans[spans.length - 1];
      var isContinuouslySimilar = lastSpan.type === span.type && lastSpan.subtype === span.subtype && lastSpan.action === span.action && lastSpan.name === span.name && span.duration() / transDuration < threshold && (span._start - lastSpan._end) / transDuration < threshold;
      var isLastSpan = originalSpans.length === index + 1;

      if (isContinuouslySimilar) {
        lastCount++;
        lastSpan._end = span._end;
      }

      if (lastCount > 1 && (!isContinuouslySimilar || isLastSpan)) {
        lastSpan.name = lastCount + 'x ' + lastSpan.name;
        lastCount = 1;
      }

      if (!isContinuouslySimilar) {
        spans.push(span);
      }
    }
  });
  return spans;
}
function adjustTransaction(transaction) {
  if (transaction.sampled) {
    var filterdSpans = transaction.spans.filter(function (span) {
      return span.duration() > 0 && span._start >= transaction._start && span._end <= transaction._end;
    });

    if (transaction.isManaged()) {
      var duration = transaction.duration();
      var similarSpans = groupSmallContinuouslySimilarSpans(filterdSpans, duration, SIMILAR_SPAN_TO_TRANSACTION_RATIO);
      transaction.spans = similarSpans;
    } else {
      transaction.spans = filterdSpans;
    }
  } else {
    transaction.resetFields();
  }

  return transaction;
}

var PerformanceMonitoring = function () {
  function PerformanceMonitoring(apmServer, configService, loggingService, transactionService) {
    this._apmServer = apmServer;
    this._configService = configService;
    this._logginService = loggingService;
    this._transactionService = transactionService;
  }

  var _proto = PerformanceMonitoring.prototype;

  _proto.init = function init(flags) {
    var _this = this;

    if (flags === void 0) {
      flags = {};
    }

    this._configService.events.observe(_common_constants__WEBPACK_IMPORTED_MODULE_0__.TRANSACTION_END + _common_constants__WEBPACK_IMPORTED_MODULE_0__.AFTER_EVENT, function (tr) {
      var payload = _this.createTransactionPayload(tr);

      if (payload) {
        _this._apmServer.addTransaction(payload);

        _this._configService.dispatchEvent(_common_constants__WEBPACK_IMPORTED_MODULE_0__.QUEUE_ADD_TRANSACTION);
      }
    });

    if (flags[_common_constants__WEBPACK_IMPORTED_MODULE_0__.HISTORY]) {
      _common_patching__WEBPACK_IMPORTED_MODULE_1__.patchEventHandler.observe(_common_constants__WEBPACK_IMPORTED_MODULE_0__.HISTORY, this.getHistorySub());
    }

    if (flags[_common_constants__WEBPACK_IMPORTED_MODULE_0__.XMLHTTPREQUEST]) {
      _common_patching__WEBPACK_IMPORTED_MODULE_1__.patchEventHandler.observe(_common_constants__WEBPACK_IMPORTED_MODULE_0__.XMLHTTPREQUEST, this.getXHRSub());
    }

    if (flags[_common_constants__WEBPACK_IMPORTED_MODULE_0__.FETCH]) {
      _common_patching__WEBPACK_IMPORTED_MODULE_1__.patchEventHandler.observe(_common_constants__WEBPACK_IMPORTED_MODULE_0__.FETCH, this.getFetchSub());
    }
  };

  _proto.getHistorySub = function getHistorySub() {
    var transactionService = this._transactionService;
    return function (event, task) {
      if (task.source === _common_constants__WEBPACK_IMPORTED_MODULE_0__.HISTORY && event === _common_constants__WEBPACK_IMPORTED_MODULE_0__.INVOKE) {
        transactionService.startTransaction(task.data.title, 'route-change', {
          managed: true,
          canReuse: true
        });
      }
    };
  };

  _proto.getXHRSub = function getXHRSub() {
    var _this2 = this;

    return function (event, task) {
      if (task.source === _common_constants__WEBPACK_IMPORTED_MODULE_0__.XMLHTTPREQUEST && !_common_patching_patch_utils__WEBPACK_IMPORTED_MODULE_2__.globalState.fetchInProgress) {
        _this2.processAPICalls(event, task);
      }
    };
  };

  _proto.getFetchSub = function getFetchSub() {
    var _this3 = this;

    return function (event, task) {
      if (task.source === _common_constants__WEBPACK_IMPORTED_MODULE_0__.FETCH) {
        _this3.processAPICalls(event, task);
      }
    };
  };

  _proto.processAPICalls = function processAPICalls(event, task) {
    var configService = this._configService;
    var transactionService = this._transactionService;

    if (task.data && task.data.url) {
      var endpoints = this._apmServer.getEndpoints();

      var isOwnEndpoint = Object.keys(endpoints).some(function (endpoint) {
        return task.data.url.indexOf(endpoints[endpoint]) !== -1;
      });

      if (isOwnEndpoint) {
        return;
      }
    }

    if (event === _common_constants__WEBPACK_IMPORTED_MODULE_0__.SCHEDULE && task.data) {
      var data = task.data;
      var requestUrl = new _common_url__WEBPACK_IMPORTED_MODULE_3__.Url(data.url);
      var spanName = data.method + ' ' + (requestUrl.relative ? requestUrl.path : (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.stripQueryStringFromUrl)(requestUrl.href));

      if (!transactionService.getCurrentTransaction()) {
        transactionService.startTransaction(spanName, _common_constants__WEBPACK_IMPORTED_MODULE_0__.HTTP_REQUEST_TYPE, {
          managed: true
        });
      }

      var span = transactionService.startSpan(spanName, 'external.http', {
        blocking: true
      });

      if (!span) {
        return;
      }

      var isDtEnabled = configService.get('distributedTracing');
      var dtOrigins = configService.get('distributedTracingOrigins');
      var currentUrl = new _common_url__WEBPACK_IMPORTED_MODULE_3__.Url(window.location.href);
      var isSameOrigin = (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.checkSameOrigin)(requestUrl.origin, currentUrl.origin) || (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.checkSameOrigin)(requestUrl.origin, dtOrigins);
      var target = data.target;

      if (isDtEnabled && isSameOrigin && target) {
        this.injectDtHeader(span, target);
        var propagateTracestate = configService.get('propagateTracestate');

        if (propagateTracestate) {
          this.injectTSHeader(span, target);
        }
      } else if (_state__WEBPACK_IMPORTED_MODULE_5__.__DEV__) {
        this._logginService.debug("Could not inject distributed tracing header to the request origin ('" + requestUrl.origin + "') from the current origin ('" + currentUrl.origin + "')");
      }

      if (data.sync) {
        span.sync = data.sync;
      }

      data.span = span;
    } else if (event === _common_constants__WEBPACK_IMPORTED_MODULE_0__.INVOKE) {
      var _data = task.data;

      if (_data && _data.span) {
        var _span = _data.span,
            response = _data.response,
            _target = _data.target;
        var status;

        if (response) {
          status = response.status;
        } else {
          status = _target.status;
        }

        var outcome;

        if (_data.status != 'abort' && !_data.aborted) {
          if (status >= 400 || status == 0) {
            outcome = _common_constants__WEBPACK_IMPORTED_MODULE_0__.OUTCOME_FAILURE;
          } else {
            outcome = _common_constants__WEBPACK_IMPORTED_MODULE_0__.OUTCOME_SUCCESS;
          }
        } else {
          outcome = _common_constants__WEBPACK_IMPORTED_MODULE_0__.OUTCOME_UNKNOWN;
        }

        _span.outcome = outcome;
        var tr = transactionService.getCurrentTransaction();

        if (tr && tr.type === _common_constants__WEBPACK_IMPORTED_MODULE_0__.HTTP_REQUEST_TYPE) {
          tr.outcome = outcome;
        }

        transactionService.endSpan(_span, _data);
      }
    }
  };

  _proto.injectDtHeader = function injectDtHeader(span, target) {
    var headerName = this._configService.get('distributedTracingHeaderName');

    var headerValue = (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.getDtHeaderValue)(span);
    var isHeaderValid = (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.isDtHeaderValid)(headerValue);

    if (isHeaderValid && headerValue && headerName) {
      (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.setRequestHeader)(target, headerName, headerValue);
    }
  };

  _proto.injectTSHeader = function injectTSHeader(span, target) {
    var headerValue = (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.getTSHeaderValue)(span);

    if (headerValue) {
      (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.setRequestHeader)(target, 'tracestate', headerValue);
    }
  };

  _proto.extractDtHeader = function extractDtHeader(target) {
    var configService = this._configService;
    var headerName = configService.get('distributedTracingHeaderName');

    if (target) {
      return (0,_common_utils__WEBPACK_IMPORTED_MODULE_4__.parseDtHeaderValue)(target[headerName]);
    }
  };

  _proto.filterTransaction = function filterTransaction(tr) {
    var duration = tr.duration();

    if (!duration) {
      if (_state__WEBPACK_IMPORTED_MODULE_5__.__DEV__) {
        var message = "transaction(" + tr.id + ", " + tr.name + ") was discarded! ";

        if (duration === 0) {
          message += "Transaction duration is 0";
        } else {
          message += "Transaction wasn't ended";
        }

        this._logginService.debug(message);
      }

      return false;
    }

    if (tr.isManaged()) {
      if (duration > TRANSACTION_DURATION_THRESHOLD) {
        if (_state__WEBPACK_IMPORTED_MODULE_5__.__DEV__) {
          this._logginService.debug("transaction(" + tr.id + ", " + tr.name + ") was discarded! Transaction duration (" + duration + ") is greater than managed transaction threshold (" + TRANSACTION_DURATION_THRESHOLD + ")");
        }

        return false;
      }

      if (tr.sampled && tr.spans.length === 0) {
        if (_state__WEBPACK_IMPORTED_MODULE_5__.__DEV__) {
          this._logginService.debug("transaction(" + tr.id + ", " + tr.name + ") was discarded! Transaction does not have any spans");
        }

        return false;
      }
    }

    return true;
  };

  _proto.createTransactionDataModel = function createTransactionDataModel(transaction) {
    var transactionStart = transaction._start;
    var spans = transaction.spans.map(function (span) {
      var spanData = {
        id: span.id,
        transaction_id: transaction.id,
        parent_id: span.parentId || transaction.id,
        trace_id: transaction.traceId,
        name: span.name,
        type: span.type,
        subtype: span.subtype,
        action: span.action,
        sync: span.sync,
        start: parseInt(span._start - transactionStart),
        duration: span.duration(),
        context: span.context,
        outcome: span.outcome,
        sample_rate: span.sampleRate
      };
      return (0,_common_truncate__WEBPACK_IMPORTED_MODULE_6__.truncateModel)(_common_truncate__WEBPACK_IMPORTED_MODULE_6__.SPAN_MODEL, spanData);
    });
    var transactionData = {
      id: transaction.id,
      trace_id: transaction.traceId,
      session: transaction.session,
      name: transaction.name,
      type: transaction.type,
      duration: transaction.duration(),
      spans: spans,
      context: transaction.context,
      marks: transaction.marks,
      breakdown: transaction.breakdownTimings,
      span_count: {
        started: spans.length
      },
      sampled: transaction.sampled,
      sample_rate: transaction.sampleRate,
      experience: transaction.experience,
      outcome: transaction.outcome
    };
    return (0,_common_truncate__WEBPACK_IMPORTED_MODULE_6__.truncateModel)(_common_truncate__WEBPACK_IMPORTED_MODULE_6__.TRANSACTION_MODEL, transactionData);
  };

  _proto.createTransactionPayload = function createTransactionPayload(transaction) {
    var adjustedTransaction = adjustTransaction(transaction);
    var filtered = this.filterTransaction(adjustedTransaction);

    if (filtered) {
      return this.createTransactionDataModel(transaction);
    }
  };

  return PerformanceMonitoring;
}();



/***/ }),

/***/ "../rum-core/dist/es/performance-monitoring/span-base.js":
/*!***************************************************************!*\
  !*** ../rum-core/dist/es/performance-monitoring/span-base.js ***!
  \***************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");



var SpanBase = function () {
  function SpanBase(name, type, options) {
    if (options === void 0) {
      options = {};
    }

    if (!name) {
      name = _common_constants__WEBPACK_IMPORTED_MODULE_0__.NAME_UNKNOWN;
    }

    if (!type) {
      type = _common_constants__WEBPACK_IMPORTED_MODULE_0__.TYPE_CUSTOM;
    }

    this.name = name;
    this.type = type;
    this.options = options;
    this.id = options.id || (0,_common_utils__WEBPACK_IMPORTED_MODULE_1__.generateRandomId)(16);
    this.traceId = options.traceId;
    this.sampled = options.sampled;
    this.sampleRate = options.sampleRate;
    this.timestamp = options.timestamp;
    this._start = (0,_common_utils__WEBPACK_IMPORTED_MODULE_1__.getTime)(options.startTime);
    this._end = undefined;
    this.ended = false;
    this.outcome = undefined;
    this.onEnd = options.onEnd;
  }

  var _proto = SpanBase.prototype;

  _proto.ensureContext = function ensureContext() {
    if (!this.context) {
      this.context = {};
    }
  };

  _proto.addLabels = function addLabels(tags) {
    this.ensureContext();
    var ctx = this.context;

    if (!ctx.tags) {
      ctx.tags = {};
    }

    var keys = Object.keys(tags);
    keys.forEach(function (k) {
      return (0,_common_utils__WEBPACK_IMPORTED_MODULE_1__.setLabel)(k, tags[k], ctx.tags);
    });
  };

  _proto.addContext = function addContext() {
    for (var _len = arguments.length, context = new Array(_len), _key = 0; _key < _len; _key++) {
      context[_key] = arguments[_key];
    }

    if (context.length === 0) return;
    this.ensureContext();
    _common_utils__WEBPACK_IMPORTED_MODULE_1__.merge.apply(void 0, [this.context].concat(context));
  };

  _proto.end = function end(endTime) {
    if (this.ended) {
      return;
    }

    this.ended = true;
    this._end = (0,_common_utils__WEBPACK_IMPORTED_MODULE_1__.getTime)(endTime);
    this.callOnEnd();
  };

  _proto.callOnEnd = function callOnEnd() {
    if (typeof this.onEnd === 'function') {
      this.onEnd(this);
    }
  };

  _proto.duration = function duration() {
    return (0,_common_utils__WEBPACK_IMPORTED_MODULE_1__.getDuration)(this._start, this._end);
  };

  return SpanBase;
}();

/* harmony default export */ __webpack_exports__["default"] = (SpanBase);

/***/ }),

/***/ "../rum-core/dist/es/performance-monitoring/span.js":
/*!**********************************************************!*\
  !*** ../rum-core/dist/es/performance-monitoring/span.js ***!
  \**********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _span_base__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./span-base */ "../rum-core/dist/es/performance-monitoring/span-base.js");
/* harmony import */ var _common_context__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../common/context */ "../rum-core/dist/es/common/context.js");
function _inheritsLoose(subClass, superClass) {
  subClass.prototype = Object.create(superClass.prototype);
  subClass.prototype.constructor = subClass;

  _setPrototypeOf(subClass, superClass);
}

function _setPrototypeOf(o, p) {
  _setPrototypeOf = Object.setPrototypeOf || function _setPrototypeOf(o, p) {
    o.__proto__ = p;
    return o;
  };

  return _setPrototypeOf(o, p);
}




var Span = function (_SpanBase) {
  _inheritsLoose(Span, _SpanBase);

  function Span(name, type, options) {
    var _this;

    _this = _SpanBase.call(this, name, type, options) || this;
    _this.parentId = _this.options.parentId;
    _this.subtype = undefined;
    _this.action = undefined;

    if (_this.type.indexOf('.') !== -1) {
      var fields = _this.type.split('.', 3);

      _this.type = fields[0];
      _this.subtype = fields[1];
      _this.action = fields[2];
    }

    _this.sync = _this.options.sync;
    return _this;
  }

  var _proto = Span.prototype;

  _proto.end = function end(endTime, data) {
    _SpanBase.prototype.end.call(this, endTime);

    (0,_common_context__WEBPACK_IMPORTED_MODULE_0__.addSpanContext)(this, data);
  };

  return Span;
}(_span_base__WEBPACK_IMPORTED_MODULE_1__.default);

/* harmony default export */ __webpack_exports__["default"] = (Span);

/***/ }),

/***/ "../rum-core/dist/es/performance-monitoring/transaction-service.js":
/*!*************************************************************************!*\
  !*** ../rum-core/dist/es/performance-monitoring/transaction-service.js ***!
  \*************************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _common_polyfills__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! ../common/polyfills */ "../rum-core/dist/es/common/polyfills.js");
/* harmony import */ var _transaction__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./transaction */ "../rum-core/dist/es/performance-monitoring/transaction.js");
/* harmony import */ var _metrics__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./metrics */ "../rum-core/dist/es/performance-monitoring/metrics.js");
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _capture_navigation__WEBPACK_IMPORTED_MODULE_7__ = __webpack_require__(/*! ./capture-navigation */ "../rum-core/dist/es/performance-monitoring/capture-navigation.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _common_context__WEBPACK_IMPORTED_MODULE_8__ = __webpack_require__(/*! ../common/context */ "../rum-core/dist/es/common/context.js");
/* harmony import */ var _state__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ../state */ "../rum-core/dist/es/state.js");
/* harmony import */ var _common_url__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ../common/url */ "../rum-core/dist/es/common/url.js");










var TransactionService = function () {
  function TransactionService(logger, config) {
    var _this = this;

    this._config = config;
    this._logger = logger;
    this.currentTransaction = undefined;
    this.respIntervalId = undefined;
    this.recorder = new _metrics__WEBPACK_IMPORTED_MODULE_0__.PerfEntryRecorder(function (list) {
      var tr = _this.getCurrentTransaction();

      if (tr && tr.captureTimings) {
        var _tr$spans;

        var isHardNavigation = tr.type === _common_constants__WEBPACK_IMPORTED_MODULE_1__.PAGE_LOAD;

        var _captureObserverEntri = (0,_metrics__WEBPACK_IMPORTED_MODULE_0__.captureObserverEntries)(list, {
          isHardNavigation: isHardNavigation,
          trStart: isHardNavigation ? 0 : tr._start
        }),
            spans = _captureObserverEntri.spans,
            marks = _captureObserverEntri.marks;

        (_tr$spans = tr.spans).push.apply(_tr$spans, spans);

        tr.addMarks({
          agent: marks
        });
      }
    });
  }

  var _proto = TransactionService.prototype;

  _proto.createCurrentTransaction = function createCurrentTransaction(name, type, options) {
    var tr = new _transaction__WEBPACK_IMPORTED_MODULE_2__.default(name, type, options);
    this.currentTransaction = tr;
    return tr;
  };

  _proto.getCurrentTransaction = function getCurrentTransaction() {
    if (this.currentTransaction && !this.currentTransaction.ended) {
      return this.currentTransaction;
    }
  };

  _proto.createOptions = function createOptions(options) {
    var config = this._config.config;
    var presetOptions = {
      transactionSampleRate: config.transactionSampleRate
    };
    var perfOptions = (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.extend)(presetOptions, options);

    if (perfOptions.managed) {
      perfOptions = (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.extend)({
        pageLoadTraceId: config.pageLoadTraceId,
        pageLoadSampled: config.pageLoadSampled,
        pageLoadSpanId: config.pageLoadSpanId,
        pageLoadTransactionName: config.pageLoadTransactionName
      }, perfOptions);
    }

    return perfOptions;
  };

  _proto.startManagedTransaction = function startManagedTransaction(name, type, perfOptions) {
    var tr = this.getCurrentTransaction();
    var isRedefined = false;

    if (!tr) {
      tr = this.createCurrentTransaction(name, type, perfOptions);
    } else if (tr.canReuse() && perfOptions.canReuse) {
      var redefineType = tr.type;
      var currentTypeOrder = _common_constants__WEBPACK_IMPORTED_MODULE_1__.TRANSACTION_TYPE_ORDER.indexOf(tr.type);
      var redefineTypeOrder = _common_constants__WEBPACK_IMPORTED_MODULE_1__.TRANSACTION_TYPE_ORDER.indexOf(type);

      if (currentTypeOrder >= 0 && redefineTypeOrder < currentTypeOrder) {
        redefineType = type;
      }

      if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
        this._logger.debug("redefining transaction(" + tr.id + ", " + tr.name + ", " + tr.type + ")", 'to', "(" + (name || tr.name) + ", " + redefineType + ")", tr);
      }

      tr.redefine(name, redefineType, perfOptions);
      isRedefined = true;
    } else {
      if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
        this._logger.debug("ending previous transaction(" + tr.id + ", " + tr.name + ")", tr);
      }

      tr.end();
      tr = this.createCurrentTransaction(name, type, perfOptions);
    }

    if (tr.type === _common_constants__WEBPACK_IMPORTED_MODULE_1__.PAGE_LOAD) {
      if (!isRedefined) {
        this.recorder.start(_common_constants__WEBPACK_IMPORTED_MODULE_1__.LARGEST_CONTENTFUL_PAINT);
        this.recorder.start(_common_constants__WEBPACK_IMPORTED_MODULE_1__.PAINT);
        this.recorder.start(_common_constants__WEBPACK_IMPORTED_MODULE_1__.FIRST_INPUT);
        this.recorder.start(_common_constants__WEBPACK_IMPORTED_MODULE_1__.LAYOUT_SHIFT);
      }

      if (perfOptions.pageLoadTraceId) {
        tr.traceId = perfOptions.pageLoadTraceId;
      }

      if (perfOptions.pageLoadSampled) {
        tr.sampled = perfOptions.pageLoadSampled;
      }

      if (tr.name === _common_constants__WEBPACK_IMPORTED_MODULE_1__.NAME_UNKNOWN && perfOptions.pageLoadTransactionName) {
        tr.name = perfOptions.pageLoadTransactionName;
      }
    }

    if (!isRedefined && this._config.get('monitorLongtasks')) {
      this.recorder.start(_common_constants__WEBPACK_IMPORTED_MODULE_1__.LONG_TASK);
    }

    if (tr.sampled) {
      tr.captureTimings = true;
    }

    return tr;
  };

  _proto.startTransaction = function startTransaction(name, type, options) {
    var _this2 = this;

    var perfOptions = this.createOptions(options);
    var tr;
    var fireOnstartHook = true;

    if (perfOptions.managed) {
      var current = this.currentTransaction;
      tr = this.startManagedTransaction(name, type, perfOptions);

      if (current === tr) {
        fireOnstartHook = false;
      }
    } else {
      tr = new _transaction__WEBPACK_IMPORTED_MODULE_2__.default(name, type, perfOptions);
    }

    tr.onEnd = function () {
      return _this2.handleTransactionEnd(tr);
    };

    if (fireOnstartHook) {
      if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
        this._logger.debug("startTransaction(" + tr.id + ", " + tr.name + ", " + tr.type + ")");
      }

      this._config.events.send(_common_constants__WEBPACK_IMPORTED_MODULE_1__.TRANSACTION_START, [tr]);
    }

    return tr;
  };

  _proto.handleTransactionEnd = function handleTransactionEnd(tr) {
    var _this3 = this;

    this.recorder.stop();
    var currentUrl = window.location.href;
    return _common_polyfills__WEBPACK_IMPORTED_MODULE_5__.Promise.resolve().then(function () {
      var name = tr.name,
          type = tr.type;
      var lastHiddenStart = _state__WEBPACK_IMPORTED_MODULE_4__.state.lastHiddenStart;

      if (lastHiddenStart >= tr._start) {
        if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
          _this3._logger.debug("transaction(" + tr.id + ", " + name + ", " + type + ") was discarded! The page was hidden during the transaction!");
        }

        return;
      }

      if (_this3.shouldIgnoreTransaction(name) || type === _common_constants__WEBPACK_IMPORTED_MODULE_1__.TEMPORARY_TYPE) {
        if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
          _this3._logger.debug("transaction(" + tr.id + ", " + name + ", " + type + ") is ignored");
        }

        return;
      }

      if (type === _common_constants__WEBPACK_IMPORTED_MODULE_1__.PAGE_LOAD) {
        var pageLoadTransactionName = _this3._config.get('pageLoadTransactionName');

        if (name === _common_constants__WEBPACK_IMPORTED_MODULE_1__.NAME_UNKNOWN && pageLoadTransactionName) {
          tr.name = pageLoadTransactionName;
        }

        if (tr.captureTimings) {
          var cls = _metrics__WEBPACK_IMPORTED_MODULE_0__.metrics.cls,
              fid = _metrics__WEBPACK_IMPORTED_MODULE_0__.metrics.fid,
              tbt = _metrics__WEBPACK_IMPORTED_MODULE_0__.metrics.tbt,
              longtask = _metrics__WEBPACK_IMPORTED_MODULE_0__.metrics.longtask;

          if (tbt.duration > 0) {
            tr.spans.push((0,_metrics__WEBPACK_IMPORTED_MODULE_0__.createTotalBlockingTimeSpan)(tbt));
          }

          tr.experience = {};

          if ((0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.isPerfTypeSupported)(_common_constants__WEBPACK_IMPORTED_MODULE_1__.LONG_TASK)) {
            tr.experience.tbt = tbt.duration;
          }

          if ((0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.isPerfTypeSupported)(_common_constants__WEBPACK_IMPORTED_MODULE_1__.LAYOUT_SHIFT)) {
            tr.experience.cls = cls.score;
          }

          if (fid > 0) {
            tr.experience.fid = fid;
          }

          if (longtask.count > 0) {
            tr.experience.longtask = {
              count: longtask.count,
              sum: longtask.duration,
              max: longtask.max
            };
          }
        }

        _this3.setSession(tr);
      }

      if (tr.name === _common_constants__WEBPACK_IMPORTED_MODULE_1__.NAME_UNKNOWN) {
        tr.name = (0,_common_url__WEBPACK_IMPORTED_MODULE_6__.slugifyUrl)(currentUrl);
      }

      (0,_capture_navigation__WEBPACK_IMPORTED_MODULE_7__.captureNavigation)(tr);

      _this3.adjustTransactionTime(tr);

      var breakdownMetrics = _this3._config.get('breakdownMetrics');

      if (breakdownMetrics) {
        tr.captureBreakdown();
      }

      var configContext = _this3._config.get('context');

      (0,_common_context__WEBPACK_IMPORTED_MODULE_8__.addTransactionContext)(tr, configContext);

      _this3._config.events.send(_common_constants__WEBPACK_IMPORTED_MODULE_1__.TRANSACTION_END, [tr]);

      if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
        _this3._logger.debug("end transaction(" + tr.id + ", " + tr.name + ", " + tr.type + ")", tr);
      }
    }, function (err) {
      if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
        _this3._logger.debug("error ending transaction(" + tr.id + ", " + tr.name + ")", err);
      }
    });
  };

  _proto.setSession = function setSession(tr) {
    var session = this._config.get('session');

    if (session) {
      if (typeof session == 'boolean') {
        tr.session = {
          id: (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.generateRandomId)(16),
          sequence: 1
        };
      } else {
        if (session.timestamp && Date.now() - session.timestamp > _common_constants__WEBPACK_IMPORTED_MODULE_1__.SESSION_TIMEOUT) {
          tr.session = {
            id: (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.generateRandomId)(16),
            sequence: 1
          };
        } else {
          tr.session = {
            id: session.id,
            sequence: session.sequence ? session.sequence + 1 : 1
          };
        }
      }

      var sessionConfig = {
        session: {
          id: tr.session.id,
          sequence: tr.session.sequence,
          timestamp: Date.now()
        }
      };

      this._config.setConfig(sessionConfig);

      this._config.setLocalConfig(sessionConfig, true);
    }
  };

  _proto.adjustTransactionTime = function adjustTransactionTime(transaction) {
    var spans = transaction.spans;
    var earliestSpan = (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.getEarliestSpan)(spans);

    if (earliestSpan && earliestSpan._start < transaction._start) {
      transaction._start = earliestSpan._start;
    }

    var latestSpan = (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.getLatestNonXHRSpan)(spans) || {};
    var latestSpanEnd = latestSpan._end || 0;

    if (transaction.type === _common_constants__WEBPACK_IMPORTED_MODULE_1__.PAGE_LOAD) {
      var transactionEndWithoutDelay = transaction._end - _common_constants__WEBPACK_IMPORTED_MODULE_1__.PAGE_LOAD_DELAY;
      var lcp = _metrics__WEBPACK_IMPORTED_MODULE_0__.metrics.lcp || 0;
      var latestXHRSpan = (0,_common_utils__WEBPACK_IMPORTED_MODULE_3__.getLatestXHRSpan)(spans) || {};
      var latestXHRSpanEnd = latestXHRSpan._end || 0;
      transaction._end = Math.max(latestSpanEnd, latestXHRSpanEnd, lcp, transactionEndWithoutDelay);
    } else if (latestSpanEnd > transaction._end) {
      transaction._end = latestSpanEnd;
    }

    this.truncateSpans(spans, transaction._end);
  };

  _proto.truncateSpans = function truncateSpans(spans, transactionEnd) {
    for (var i = 0; i < spans.length; i++) {
      var span = spans[i];

      if (span._end > transactionEnd) {
        span._end = transactionEnd;
        span.type += _common_constants__WEBPACK_IMPORTED_MODULE_1__.TRUNCATED_TYPE;
      }

      if (span._start > transactionEnd) {
        span._start = transactionEnd;
      }
    }
  };

  _proto.shouldIgnoreTransaction = function shouldIgnoreTransaction(transactionName) {
    var ignoreList = this._config.get('ignoreTransactions');

    if (ignoreList && ignoreList.length) {
      for (var i = 0; i < ignoreList.length; i++) {
        var element = ignoreList[i];

        if (typeof element.test === 'function') {
          if (element.test(transactionName)) {
            return true;
          }
        } else if (element === transactionName) {
          return true;
        }
      }
    }

    return false;
  };

  _proto.startSpan = function startSpan(name, type, options) {
    var tr = this.getCurrentTransaction();

    if (!tr) {
      tr = this.createCurrentTransaction(undefined, _common_constants__WEBPACK_IMPORTED_MODULE_1__.TEMPORARY_TYPE, this.createOptions({
        canReuse: true,
        managed: true
      }));
    }

    var span = tr.startSpan(name, type, options);

    if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
      this._logger.debug("startSpan(" + name + ", " + span.type + ")", "on transaction(" + tr.id + ", " + tr.name + ")");
    }

    return span;
  };

  _proto.endSpan = function endSpan(span, context) {
    if (!span) {
      return;
    }

    if (_state__WEBPACK_IMPORTED_MODULE_4__.__DEV__) {
      var tr = this.getCurrentTransaction();
      tr && this._logger.debug("endSpan(" + span.name + ", " + span.type + ")", "on transaction(" + tr.id + ", " + tr.name + ")");
    }

    span.end(null, context);
  };

  return TransactionService;
}();

/* harmony default export */ __webpack_exports__["default"] = (TransactionService);

/***/ }),

/***/ "../rum-core/dist/es/performance-monitoring/transaction.js":
/*!*****************************************************************!*\
  !*** ../rum-core/dist/es/performance-monitoring/transaction.js ***!
  \*****************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _span__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./span */ "../rum-core/dist/es/performance-monitoring/span.js");
/* harmony import */ var _span_base__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! ./span-base */ "../rum-core/dist/es/performance-monitoring/span-base.js");
/* harmony import */ var _common_utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../common/utils */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _common_constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../common/constants */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _breakdown__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./breakdown */ "../rum-core/dist/es/performance-monitoring/breakdown.js");
function _inheritsLoose(subClass, superClass) {
  subClass.prototype = Object.create(superClass.prototype);
  subClass.prototype.constructor = subClass;

  _setPrototypeOf(subClass, superClass);
}

function _setPrototypeOf(o, p) {
  _setPrototypeOf = Object.setPrototypeOf || function _setPrototypeOf(o, p) {
    o.__proto__ = p;
    return o;
  };

  return _setPrototypeOf(o, p);
}







var Transaction = function (_SpanBase) {
  _inheritsLoose(Transaction, _SpanBase);

  function Transaction(name, type, options) {
    var _this;

    _this = _SpanBase.call(this, name, type, options) || this;
    _this.traceId = (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.generateRandomId)();
    _this.marks = undefined;
    _this.spans = [];
    _this._activeSpans = {};
    _this._activeTasks = new Set();
    _this.blocked = false;
    _this.captureTimings = false;
    _this.breakdownTimings = [];
    _this.sampleRate = _this.options.transactionSampleRate;
    _this.sampled = Math.random() <= _this.sampleRate;
    return _this;
  }

  var _proto = Transaction.prototype;

  _proto.addMarks = function addMarks(obj) {
    this.marks = (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.merge)(this.marks || {}, obj);
  };

  _proto.mark = function mark(key) {
    var skey = (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.removeInvalidChars)(key);

    var markTime = (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.now)() - this._start;

    var custom = {};
    custom[skey] = markTime;
    this.addMarks({
      custom: custom
    });
  };

  _proto.canReuse = function canReuse() {
    var threshold = this.options.reuseThreshold || _common_constants__WEBPACK_IMPORTED_MODULE_1__.REUSABILITY_THRESHOLD;
    return !!this.options.canReuse && !this.ended && (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.now)() - this._start < threshold;
  };

  _proto.redefine = function redefine(name, type, options) {
    if (name) {
      this.name = name;
    }

    if (type) {
      this.type = type;
    }

    if (options) {
      this.options.reuseThreshold = options.reuseThreshold;
      (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.extend)(this.options, options);
    }
  };

  _proto.startSpan = function startSpan(name, type, options) {
    var _this2 = this;

    if (this.ended) {
      return;
    }

    var opts = (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.extend)({}, options);

    opts.onEnd = function (trc) {
      _this2._onSpanEnd(trc);
    };

    opts.traceId = this.traceId;
    opts.sampled = this.sampled;
    opts.sampleRate = this.sampleRate;

    if (!opts.parentId) {
      opts.parentId = this.id;
    }

    var span = new _span__WEBPACK_IMPORTED_MODULE_2__.default(name, type, opts);
    this._activeSpans[span.id] = span;

    if (opts.blocking) {
      this.addTask(span.id);
    }

    return span;
  };

  _proto.isFinished = function isFinished() {
    return !this.blocked && this._activeTasks.size === 0;
  };

  _proto.detectFinish = function detectFinish() {
    if (this.isFinished()) this.end();
  };

  _proto.end = function end(endTime) {
    if (this.ended) {
      return;
    }

    this.ended = true;
    this._end = (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.getTime)(endTime);

    for (var sid in this._activeSpans) {
      var span = this._activeSpans[sid];
      span.type = span.type + _common_constants__WEBPACK_IMPORTED_MODULE_1__.TRUNCATED_TYPE;
      span.end(endTime);
    }

    this.callOnEnd();
  };

  _proto.captureBreakdown = function captureBreakdown() {
    this.breakdownTimings = (0,_breakdown__WEBPACK_IMPORTED_MODULE_3__.captureBreakdown)(this);
  };

  _proto.block = function block(flag) {
    this.blocked = flag;

    if (!this.blocked) {
      this.detectFinish();
    }
  };

  _proto.addTask = function addTask(taskId) {
    if (!taskId) {
      taskId = 'task-' + (0,_common_utils__WEBPACK_IMPORTED_MODULE_0__.generateRandomId)(16);
    }

    this._activeTasks.add(taskId);

    return taskId;
  };

  _proto.removeTask = function removeTask(taskId) {
    var deleted = this._activeTasks.delete(taskId);

    deleted && this.detectFinish();
  };

  _proto.resetFields = function resetFields() {
    this.spans = [];
    this.sampleRate = 0;
  };

  _proto._onSpanEnd = function _onSpanEnd(span) {
    this.spans.push(span);
    delete this._activeSpans[span.id];
    this.removeTask(span.id);
  };

  _proto.isManaged = function isManaged() {
    return !!this.options.managed;
  };

  return Transaction;
}(_span_base__WEBPACK_IMPORTED_MODULE_4__.default);

/* harmony default export */ __webpack_exports__["default"] = (Transaction);

/***/ }),

/***/ "../rum-core/dist/es/state.js":
/*!************************************!*\
  !*** ../rum-core/dist/es/state.js ***!
  \************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "__DEV__": function() { return /* binding */ __DEV__; },
/* harmony export */   "state": function() { return /* binding */ state; }
/* harmony export */ });
var __DEV__ = "development" !== 'production';

var state = {
  bootstrapTime: null,
  lastHiddenStart: Number.MIN_SAFE_INTEGER
};


/***/ }),

/***/ "./src/apm-base.js":
/*!*************************!*\
  !*** ./src/apm-base.js ***!
  \*************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": function() { return /* binding */ ApmBase; }
/* harmony export */ });
/* harmony import */ var _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @elastic/apm-rum-core */ "../rum-core/dist/es/common/constants.js");
/* harmony import */ var _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @elastic/apm-rum-core */ "../rum-core/dist/es/common/instrument.js");
/* harmony import */ var _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @elastic/apm-rum-core */ "../rum-core/dist/es/common/observers/page-visibility.js");
/* harmony import */ var _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @elastic/apm-rum-core */ "../rum-core/dist/es/common/observers/page-clicks.js");


var ApmBase = function () {
  function ApmBase(serviceFactory, disable) {
    this._disable = disable;
    this.serviceFactory = serviceFactory;
    this._initialized = false;
  }

  var _proto = ApmBase.prototype;

  _proto.isEnabled = function isEnabled() {
    return !this._disable;
  };

  _proto.isActive = function isActive() {
    var configService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE);
    return this.isEnabled() && this._initialized && configService.get('active');
  };

  _proto.init = function init(config) {
    var _this = this;

    if (this.isEnabled() && !this._initialized) {
      this._initialized = true;

      var _this$serviceFactory$ = this.serviceFactory.getService([_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE, _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.LOGGING_SERVICE, _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.TRANSACTION_SERVICE]),
          configService = _this$serviceFactory$[0],
          loggingService = _this$serviceFactory$[1],
          transactionService = _this$serviceFactory$[2];

      configService.setVersion('5.12.0');
      this.config(config);
      var logLevel = configService.get('logLevel');
      loggingService.setLevel(logLevel);
      var isConfigActive = configService.get('active');

      if (isConfigActive) {
        this.serviceFactory.init();
        var flags = (0,_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_1__.getInstrumentationFlags)(configService.get('instrument'), configService.get('disableInstrumentations'));
        var performanceMonitoring = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.PERFORMANCE_MONITORING);
        performanceMonitoring.init(flags);

        if (flags[_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.ERROR]) {
          var errorLogging = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.ERROR_LOGGING);
          errorLogging.registerListeners();
        }

        if (configService.get('session')) {
          var localConfig = configService.getLocalConfig();

          if (localConfig && localConfig.session) {
            configService.setConfig({
              session: localConfig.session
            });
          }
        }

        var sendPageLoad = function sendPageLoad() {
          return flags[_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.PAGE_LOAD] && _this._sendPageLoadMetrics();
        };

        if (configService.get('centralConfig')) {
          this.fetchCentralConfig().then(sendPageLoad);
        } else {
          sendPageLoad();
        }

        (0,_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_2__.observePageVisibility)(configService, transactionService);

        if (flags[_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.EVENT_TARGET] && flags[_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CLICK]) {
          (0,_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_3__.observePageClicks)(transactionService);
        }
      } else {
        this._disable = true;
        loggingService.warn('RUM agent is inactive');
      }
    }

    return this;
  };

  _proto.fetchCentralConfig = function fetchCentralConfig() {
    var _this$serviceFactory$2 = this.serviceFactory.getService([_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.APM_SERVER, _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.LOGGING_SERVICE, _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE]),
        apmServer = _this$serviceFactory$2[0],
        loggingService = _this$serviceFactory$2[1],
        configService = _this$serviceFactory$2[2];

    return apmServer.fetchConfig(configService.get('serviceName'), configService.get('environment')).then(function (config) {
      var transactionSampleRate = config['transaction_sample_rate'];

      if (transactionSampleRate) {
        transactionSampleRate = Number(transactionSampleRate);
        var _config2 = {
          transactionSampleRate: transactionSampleRate
        };

        var _configService$valida = configService.validate(_config2),
            invalid = _configService$valida.invalid;

        if (invalid.length === 0) {
          configService.setConfig(_config2);
        } else {
          var _invalid$ = invalid[0],
              key = _invalid$.key,
              value = _invalid$.value,
              allowed = _invalid$.allowed;
          loggingService.warn("invalid value \"" + value + "\" for " + key + ". Allowed: " + allowed + ".");
        }
      }

      return config;
    }).catch(function (error) {
      loggingService.warn('failed fetching config:', error);
    });
  };

  _proto._sendPageLoadMetrics = function _sendPageLoadMetrics() {
    var tr = this.startTransaction(undefined, _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.PAGE_LOAD, {
      managed: true,
      canReuse: true
    });

    if (!tr) {
      return;
    }

    tr.addTask(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.PAGE_LOAD);

    var sendPageLoadMetrics = function sendPageLoadMetrics() {
      setTimeout(function () {
        return tr.removeTask(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.PAGE_LOAD);
      }, _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.PAGE_LOAD_DELAY);
    };

    if (document.readyState === 'complete') {
      sendPageLoadMetrics();
    } else {
      window.addEventListener('load', sendPageLoadMetrics);
    }
  };

  _proto.observe = function observe(name, fn) {
    var configService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE);
    configService.events.observe(name, fn);
  };

  _proto.config = function config(_config) {
    var _this$serviceFactory$3 = this.serviceFactory.getService([_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE, _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.LOGGING_SERVICE]),
        configService = _this$serviceFactory$3[0],
        loggingService = _this$serviceFactory$3[1];

    var _configService$valida2 = configService.validate(_config),
        missing = _configService$valida2.missing,
        invalid = _configService$valida2.invalid,
        unknown = _configService$valida2.unknown;

    if (unknown.length > 0) {
      var message = 'Unknown config options are specified for RUM agent: ' + unknown.join(', ');
      loggingService.warn(message);
    }

    if (missing.length === 0 && invalid.length === 0) {
      configService.setConfig(_config);
    } else {
      var separator = ', ';
      var _message = "RUM agent isn't correctly configured. ";

      if (missing.length > 0) {
        _message += missing.join(separator) + ' is missing';

        if (invalid.length > 0) {
          _message += separator;
        }
      }

      invalid.forEach(function (_ref, index) {
        var key = _ref.key,
            value = _ref.value,
            allowed = _ref.allowed;
        _message += key + " \"" + value + "\" contains invalid characters! (allowed: " + allowed + ")" + (index !== invalid.length - 1 ? separator : '');
      });
      loggingService.error(_message);
      configService.setConfig({
        active: false
      });
    }
  };

  _proto.setUserContext = function setUserContext(userContext) {
    var configService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE);
    configService.setUserContext(userContext);
  };

  _proto.setCustomContext = function setCustomContext(customContext) {
    var configService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE);
    configService.setCustomContext(customContext);
  };

  _proto.addLabels = function addLabels(labels) {
    var configService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE);
    configService.addLabels(labels);
  };

  _proto.setInitialPageLoadName = function setInitialPageLoadName(name) {
    var configService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE);
    configService.setConfig({
      pageLoadTransactionName: name
    });
  };

  _proto.startTransaction = function startTransaction(name, type, options) {
    if (this.isEnabled()) {
      var transactionService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.TRANSACTION_SERVICE);
      return transactionService.startTransaction(name, type, options);
    }
  };

  _proto.startSpan = function startSpan(name, type, options) {
    if (this.isEnabled()) {
      var transactionService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.TRANSACTION_SERVICE);
      return transactionService.startSpan(name, type, options);
    }
  };

  _proto.getCurrentTransaction = function getCurrentTransaction() {
    if (this.isEnabled()) {
      var transactionService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.TRANSACTION_SERVICE);
      return transactionService.getCurrentTransaction();
    }
  };

  _proto.captureError = function captureError(error) {
    if (this.isEnabled()) {
      var errorLogging = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.ERROR_LOGGING);
      return errorLogging.logError(error);
    }
  };

  _proto.addFilter = function addFilter(fn) {
    var configService = this.serviceFactory.getService(_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_0__.CONFIG_SERVICE);
    configService.addFilter(fn);
  };

  return ApmBase;
}();



/***/ }),

/***/ "../../node_modules/error-stack-parser/error-stack-parser.js":
/*!*******************************************************************!*\
  !*** ../../node_modules/error-stack-parser/error-stack-parser.js ***!
  \*******************************************************************/
/***/ (function(module, exports, __webpack_require__) {

var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;(function(root, factory) {
    'use strict';
    // Universal Module Definition (UMD) to support AMD, CommonJS/Node.js, Rhino, and browsers.

    /* istanbul ignore next */
    if (true) {
        !(__WEBPACK_AMD_DEFINE_ARRAY__ = [__webpack_require__(/*! stackframe */ "../../node_modules/stackframe/stackframe.js")], __WEBPACK_AMD_DEFINE_FACTORY__ = (factory),
		__WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ?
		(__WEBPACK_AMD_DEFINE_FACTORY__.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__)) : __WEBPACK_AMD_DEFINE_FACTORY__),
		__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
    } else {}
}(this, function ErrorStackParser(StackFrame) {
    'use strict';

    var FIREFOX_SAFARI_STACK_REGEXP = /(^|@)\S+\:\d+/;
    var CHROME_IE_STACK_REGEXP = /^\s*at .*(\S+\:\d+|\(native\))/m;
    var SAFARI_NATIVE_CODE_REGEXP = /^(eval@)?(\[native code\])?$/;

    function _map(array, fn, thisArg) {
        if (typeof Array.prototype.map === 'function') {
            return array.map(fn, thisArg);
        } else {
            var output = new Array(array.length);
            for (var i = 0; i < array.length; i++) {
                output[i] = fn.call(thisArg, array[i]);
            }
            return output;
        }
    }

    function _filter(array, fn, thisArg) {
        if (typeof Array.prototype.filter === 'function') {
            return array.filter(fn, thisArg);
        } else {
            var output = [];
            for (var i = 0; i < array.length; i++) {
                if (fn.call(thisArg, array[i])) {
                    output.push(array[i]);
                }
            }
            return output;
        }
    }

    function _indexOf(array, target) {
        if (typeof Array.prototype.indexOf === 'function') {
            return array.indexOf(target);
        } else {
            for (var i = 0; i < array.length; i++) {
                if (array[i] === target) {
                    return i;
                }
            }
            return -1;
        }
    }

    return {
        /**
         * Given an Error object, extract the most information from it.
         *
         * @param {Error} error object
         * @return {Array} of StackFrames
         */
        parse: function ErrorStackParser$$parse(error) {
            if (typeof error.stacktrace !== 'undefined' || typeof error['opera#sourceloc'] !== 'undefined') {
                return this.parseOpera(error);
            } else if (error.stack && error.stack.match(CHROME_IE_STACK_REGEXP)) {
                return this.parseV8OrIE(error);
            } else if (error.stack) {
                return this.parseFFOrSafari(error);
            } else {
                throw new Error('Cannot parse given Error object');
            }
        },

        // Separate line and column numbers from a string of the form: (URI:Line:Column)
        extractLocation: function ErrorStackParser$$extractLocation(urlLike) {
            // Fail-fast but return locations like "(native)"
            if (urlLike.indexOf(':') === -1) {
                return [urlLike];
            }

            var regExp = /(.+?)(?:\:(\d+))?(?:\:(\d+))?$/;
            var parts = regExp.exec(urlLike.replace(/[\(\)]/g, ''));
            return [parts[1], parts[2] || undefined, parts[3] || undefined];
        },

        parseV8OrIE: function ErrorStackParser$$parseV8OrIE(error) {
            var filtered = _filter(error.stack.split('\n'), function(line) {
                return !!line.match(CHROME_IE_STACK_REGEXP);
            }, this);

            return _map(filtered, function(line) {
                if (line.indexOf('(eval ') > -1) {
                    // Throw away eval information until we implement stacktrace.js/stackframe#8
                    line = line.replace(/eval code/g, 'eval').replace(/(\(eval at [^\()]*)|(\)\,.*$)/g, '');
                }
                var tokens = line.replace(/^\s+/, '').replace(/\(eval code/g, '(').split(/\s+/).slice(1);
                var locationParts = this.extractLocation(tokens.pop());
                var functionName = tokens.join(' ') || undefined;
                var fileName = _indexOf(['eval', '<anonymous>'], locationParts[0]) > -1 ? undefined : locationParts[0];

                return new StackFrame(functionName, undefined, fileName, locationParts[1], locationParts[2], line);
            }, this);
        },

        parseFFOrSafari: function ErrorStackParser$$parseFFOrSafari(error) {
            var filtered = _filter(error.stack.split('\n'), function(line) {
                return !line.match(SAFARI_NATIVE_CODE_REGEXP);
            }, this);

            return _map(filtered, function(line) {
                // Throw away eval information until we implement stacktrace.js/stackframe#8
                if (line.indexOf(' > eval') > -1) {
                    line = line.replace(/ line (\d+)(?: > eval line \d+)* > eval\:\d+\:\d+/g, ':$1');
                }

                if (line.indexOf('@') === -1 && line.indexOf(':') === -1) {
                    // Safari eval frames only have function names and nothing else
                    return new StackFrame(line);
                } else {
                    var tokens = line.split('@');
                    var locationParts = this.extractLocation(tokens.pop());
                    var functionName = tokens.join('@') || undefined;
                    return new StackFrame(functionName,
                        undefined,
                        locationParts[0],
                        locationParts[1],
                        locationParts[2],
                        line);
                }
            }, this);
        },

        parseOpera: function ErrorStackParser$$parseOpera(e) {
            if (!e.stacktrace || (e.message.indexOf('\n') > -1 &&
                e.message.split('\n').length > e.stacktrace.split('\n').length)) {
                return this.parseOpera9(e);
            } else if (!e.stack) {
                return this.parseOpera10(e);
            } else {
                return this.parseOpera11(e);
            }
        },

        parseOpera9: function ErrorStackParser$$parseOpera9(e) {
            var lineRE = /Line (\d+).*script (?:in )?(\S+)/i;
            var lines = e.message.split('\n');
            var result = [];

            for (var i = 2, len = lines.length; i < len; i += 2) {
                var match = lineRE.exec(lines[i]);
                if (match) {
                    result.push(new StackFrame(undefined, undefined, match[2], match[1], undefined, lines[i]));
                }
            }

            return result;
        },

        parseOpera10: function ErrorStackParser$$parseOpera10(e) {
            var lineRE = /Line (\d+).*script (?:in )?(\S+)(?:: In function (\S+))?$/i;
            var lines = e.stacktrace.split('\n');
            var result = [];

            for (var i = 0, len = lines.length; i < len; i += 2) {
                var match = lineRE.exec(lines[i]);
                if (match) {
                    result.push(
                        new StackFrame(
                            match[3] || undefined,
                            undefined,
                            match[2],
                            match[1],
                            undefined,
                            lines[i]
                        )
                    );
                }
            }

            return result;
        },

        // Opera 10.65+ Error.stack very similar to FF/Safari
        parseOpera11: function ErrorStackParser$$parseOpera11(error) {
            var filtered = _filter(error.stack.split('\n'), function(line) {
                return !!line.match(FIREFOX_SAFARI_STACK_REGEXP) && !line.match(/^Error created at/);
            }, this);

            return _map(filtered, function(line) {
                var tokens = line.split('@');
                var locationParts = this.extractLocation(tokens.pop());
                var functionCall = (tokens.shift() || '');
                var functionName = functionCall
                        .replace(/<anonymous function(: (\w+))?>/, '$2')
                        .replace(/\([^\)]*\)/g, '') || undefined;
                var argsRaw;
                if (functionCall.match(/\(([^\)]*)\)/)) {
                    argsRaw = functionCall.replace(/^[^\(]+\(([^\)]*)\)$/, '$1');
                }
                var args = (argsRaw === undefined || argsRaw === '[arguments not available]') ?
                    undefined : argsRaw.split(',');
                return new StackFrame(
                    functionName,
                    args,
                    locationParts[0],
                    locationParts[1],
                    locationParts[2],
                    line);
            }, this);
        }
    };
}));



/***/ }),

/***/ "../../node_modules/opentracing/lib/constants.js":
/*!*******************************************************!*\
  !*** ../../node_modules/opentracing/lib/constants.js ***!
  \*******************************************************/
/***/ (function(__unused_webpack_module, exports) {

"use strict";

Object.defineProperty(exports, "__esModule", ({ value: true }));
/**
 * The FORMAT_BINARY format represents SpanContexts in an opaque binary
 * carrier.
 *
 * Tracer.inject() will set the buffer field to an Array-like (Array,
 * ArrayBuffer, or TypedBuffer) object containing the injected binary data.
 * Any valid Object can be used as long as the buffer field of the object
 * can be set.
 *
 * Tracer.extract() will look for `carrier.buffer`, and that field is
 * expected to be an Array-like object (Array, ArrayBuffer, or
 * TypedBuffer).
 */
exports.FORMAT_BINARY = 'binary';
/**
 * The FORMAT_TEXT_MAP format represents SpanContexts using a
 * string->string map (backed by a Javascript Object) as a carrier.
 *
 * NOTE: Unlike FORMAT_HTTP_HEADERS, FORMAT_TEXT_MAP places no restrictions
 * on the characters used in either the keys or the values of the map
 * entries.
 *
 * The FORMAT_TEXT_MAP carrier map may contain unrelated data (e.g.,
 * arbitrary gRPC metadata); as such, the Tracer implementation should use
 * a prefix or other convention to distinguish Tracer-specific key:value
 * pairs.
 */
exports.FORMAT_TEXT_MAP = 'text_map';
/**
 * The FORMAT_HTTP_HEADERS format represents SpanContexts using a
 * character-restricted string->string map (backed by a Javascript Object)
 * as a carrier.
 *
 * Keys and values in the FORMAT_HTTP_HEADERS carrier must be suitable for
 * use as HTTP headers (without modification or further escaping). That is,
 * the keys have a greatly restricted character set, casing for the keys
 * may not be preserved by various intermediaries, and the values should be
 * URL-escaped.
 *
 * The FORMAT_HTTP_HEADERS carrier map may contain unrelated data (e.g.,
 * arbitrary HTTP headers); as such, the Tracer implementation should use a
 * prefix or other convention to distinguish Tracer-specific key:value
 * pairs.
 */
exports.FORMAT_HTTP_HEADERS = 'http_headers';
/**
 * A Span may be the "child of" a parent Span. In a “child of” reference,
 * the parent Span depends on the child Span in some capacity.
 *
 * See more about reference types at https://github.com/opentracing/specification
 */
exports.REFERENCE_CHILD_OF = 'child_of';
/**
 * Some parent Spans do not depend in any way on the result of their child
 * Spans. In these cases, we say merely that the child Span “follows from”
 * the parent Span in a causal sense.
 *
 * See more about reference types at https://github.com/opentracing/specification
 */
exports.REFERENCE_FOLLOWS_FROM = 'follows_from';
//# sourceMappingURL=constants.js.map

/***/ }),

/***/ "../../node_modules/opentracing/lib/functions.js":
/*!*******************************************************!*\
  !*** ../../node_modules/opentracing/lib/functions.js ***!
  \*******************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", ({ value: true }));
var Constants = __webpack_require__(/*! ./constants */ "../../node_modules/opentracing/lib/constants.js");
var reference_1 = __webpack_require__(/*! ./reference */ "../../node_modules/opentracing/lib/reference.js");
var span_1 = __webpack_require__(/*! ./span */ "../../node_modules/opentracing/lib/span.js");
/**
 * Return a new REFERENCE_CHILD_OF reference.
 *
 * @param {SpanContext} spanContext - the parent SpanContext instance to
 *        reference.
 * @return a REFERENCE_CHILD_OF reference pointing to `spanContext`
 */
function childOf(spanContext) {
    // Allow the user to pass a Span instead of a SpanContext
    if (spanContext instanceof span_1.default) {
        spanContext = spanContext.context();
    }
    return new reference_1.default(Constants.REFERENCE_CHILD_OF, spanContext);
}
exports.childOf = childOf;
/**
 * Return a new REFERENCE_FOLLOWS_FROM reference.
 *
 * @param {SpanContext} spanContext - the parent SpanContext instance to
 *        reference.
 * @return a REFERENCE_FOLLOWS_FROM reference pointing to `spanContext`
 */
function followsFrom(spanContext) {
    // Allow the user to pass a Span instead of a SpanContext
    if (spanContext instanceof span_1.default) {
        spanContext = spanContext.context();
    }
    return new reference_1.default(Constants.REFERENCE_FOLLOWS_FROM, spanContext);
}
exports.followsFrom = followsFrom;
//# sourceMappingURL=functions.js.map

/***/ }),

/***/ "../../node_modules/opentracing/lib/noop.js":
/*!**************************************************!*\
  !*** ../../node_modules/opentracing/lib/noop.js ***!
  \**************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", ({ value: true }));
var span_1 = __webpack_require__(/*! ./span */ "../../node_modules/opentracing/lib/span.js");
var span_context_1 = __webpack_require__(/*! ./span_context */ "../../node_modules/opentracing/lib/span_context.js");
var tracer_1 = __webpack_require__(/*! ./tracer */ "../../node_modules/opentracing/lib/tracer.js");
exports.tracer = null;
exports.spanContext = null;
exports.span = null;
// Deferred initialization to avoid a dependency cycle where Tracer depends on
// Span which depends on the noop tracer.
function initialize() {
    exports.tracer = new tracer_1.default();
    exports.span = new span_1.default();
    exports.spanContext = new span_context_1.default();
}
exports.initialize = initialize;
//# sourceMappingURL=noop.js.map

/***/ }),

/***/ "../../node_modules/opentracing/lib/reference.js":
/*!*******************************************************!*\
  !*** ../../node_modules/opentracing/lib/reference.js ***!
  \*******************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", ({ value: true }));
var span_1 = __webpack_require__(/*! ./span */ "../../node_modules/opentracing/lib/span.js");
/**
 * Reference pairs a reference type constant (e.g., REFERENCE_CHILD_OF or
 * REFERENCE_FOLLOWS_FROM) with the SpanContext it points to.
 *
 * See the exported childOf() and followsFrom() functions at the package level.
 */
var Reference = /** @class */ (function () {
    /**
     * Initialize a new Reference instance.
     *
     * @param {string} type - the Reference type constant (e.g.,
     *        REFERENCE_CHILD_OF or REFERENCE_FOLLOWS_FROM).
     * @param {SpanContext} referencedContext - the SpanContext being referred
     *        to. As a convenience, a Span instance may be passed in instead
     *        (in which case its .context() is used here).
     */
    function Reference(type, referencedContext) {
        this._type = type;
        this._referencedContext = (referencedContext instanceof span_1.default ?
            referencedContext.context() :
            referencedContext);
    }
    /**
     * @return {string} The Reference type (e.g., REFERENCE_CHILD_OF or
     *         REFERENCE_FOLLOWS_FROM).
     */
    Reference.prototype.type = function () {
        return this._type;
    };
    /**
     * @return {SpanContext} The SpanContext being referred to (e.g., the
     *         parent in a REFERENCE_CHILD_OF Reference).
     */
    Reference.prototype.referencedContext = function () {
        return this._referencedContext;
    };
    return Reference;
}());
exports.default = Reference;
//# sourceMappingURL=reference.js.map

/***/ }),

/***/ "../../node_modules/opentracing/lib/span.js":
/*!**************************************************!*\
  !*** ../../node_modules/opentracing/lib/span.js ***!
  \**************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", ({ value: true }));
var noop = __webpack_require__(/*! ./noop */ "../../node_modules/opentracing/lib/noop.js");
/**
 * Span represents a logical unit of work as part of a broader Trace. Examples
 * of span might include remote procedure calls or a in-process function calls
 * to sub-components. A Trace has a single, top-level "root" Span that in turn
 * may have zero or more child Spans, which in turn may have children.
 */
var Span = /** @class */ (function () {
    function Span() {
    }
    // ---------------------------------------------------------------------- //
    // OpenTracing API methods
    // ---------------------------------------------------------------------- //
    /**
     * Returns the SpanContext object associated with this Span.
     *
     * @return {SpanContext}
     */
    Span.prototype.context = function () {
        return this._context();
    };
    /**
     * Returns the Tracer object used to create this Span.
     *
     * @return {Tracer}
     */
    Span.prototype.tracer = function () {
        return this._tracer();
    };
    /**
     * Sets the string name for the logical operation this span represents.
     *
     * @param {string} name
     */
    Span.prototype.setOperationName = function (name) {
        this._setOperationName(name);
        return this;
    };
    /**
     * Sets a key:value pair on this Span that also propagates to future
     * children of the associated Span.
     *
     * setBaggageItem() enables powerful functionality given a full-stack
     * opentracing integration (e.g., arbitrary application data from a web
     * client can make it, transparently, all the way into the depths of a
     * storage system), and with it some powerful costs: use this feature with
     * care.
     *
     * IMPORTANT NOTE #1: setBaggageItem() will only propagate baggage items to
     * *future* causal descendants of the associated Span.
     *
     * IMPORTANT NOTE #2: Use this thoughtfully and with care. Every key and
     * value is copied into every local *and remote* child of the associated
     * Span, and that can add up to a lot of network and cpu overhead.
     *
     * @param {string} key
     * @param {string} value
     */
    Span.prototype.setBaggageItem = function (key, value) {
        this._setBaggageItem(key, value);
        return this;
    };
    /**
     * Returns the value for a baggage item given its key.
     *
     * @param  {string} key
     *         The key for the given trace attribute.
     * @return {string}
     *         String value for the given key, or undefined if the key does not
     *         correspond to a set trace attribute.
     */
    Span.prototype.getBaggageItem = function (key) {
        return this._getBaggageItem(key);
    };
    /**
     * Adds a single tag to the span.  See `addTags()` for details.
     *
     * @param {string} key
     * @param {any} value
     */
    Span.prototype.setTag = function (key, value) {
        // NOTE: the call is normalized to a call to _addTags()
        this._addTags((_a = {}, _a[key] = value, _a));
        return this;
        var _a;
    };
    /**
     * Adds the given key value pairs to the set of span tags.
     *
     * Multiple calls to addTags() results in the tags being the superset of
     * all calls.
     *
     * The behavior of setting the same key multiple times on the same span
     * is undefined.
     *
     * The supported type of the values is implementation-dependent.
     * Implementations are expected to safely handle all types of values but
     * may choose to ignore unrecognized / unhandle-able values (e.g. objects
     * with cyclic references, function objects).
     *
     * @return {[type]} [description]
     */
    Span.prototype.addTags = function (keyValueMap) {
        this._addTags(keyValueMap);
        return this;
    };
    /**
     * Add a log record to this Span, optionally at a user-provided timestamp.
     *
     * For example:
     *
     *     span.log({
     *         size: rpc.size(),  // numeric value
     *         URI: rpc.URI(),  // string value
     *         payload: rpc.payload(),  // Object value
     *         "keys can be arbitrary strings": rpc.foo(),
     *     });
     *
     *     span.log({
     *         "error.description": someError.description(),
     *     }, someError.timestampMillis());
     *
     * @param {object} keyValuePairs
     *        An object mapping string keys to arbitrary value types. All
     *        Tracer implementations should support bool, string, and numeric
     *        value types, and some may also support Object values.
     * @param {number} timestamp
     *        An optional parameter specifying the timestamp in milliseconds
     *        since the Unix epoch. Fractional values are allowed so that
     *        timestamps with sub-millisecond accuracy can be represented. If
     *        not specified, the implementation is expected to use its notion
     *        of the current time of the call.
     */
    Span.prototype.log = function (keyValuePairs, timestamp) {
        this._log(keyValuePairs, timestamp);
        return this;
    };
    /**
     * DEPRECATED
     */
    Span.prototype.logEvent = function (eventName, payload) {
        return this._log({ event: eventName, payload: payload });
    };
    /**
     * Sets the end timestamp and finalizes Span state.
     *
     * With the exception of calls to Span.context() (which are always allowed),
     * finish() must be the last call made to any span instance, and to do
     * otherwise leads to undefined behavior.
     *
     * @param  {number} finishTime
     *         Optional finish time in milliseconds as a Unix timestamp. Decimal
     *         values are supported for timestamps with sub-millisecond accuracy.
     *         If not specified, the current time (as defined by the
     *         implementation) will be used.
     */
    Span.prototype.finish = function (finishTime) {
        this._finish(finishTime);
        // Do not return `this`. The Span generally should not be used after it
        // is finished so chaining is not desired in this context.
    };
    // ---------------------------------------------------------------------- //
    // Derived classes can choose to implement the below
    // ---------------------------------------------------------------------- //
    // By default returns a no-op SpanContext.
    Span.prototype._context = function () {
        return noop.spanContext;
    };
    // By default returns a no-op tracer.
    //
    // The base class could store the tracer that created it, but it does not
    // in order to ensure the no-op span implementation has zero members,
    // which allows V8 to aggressively optimize calls to such objects.
    Span.prototype._tracer = function () {
        return noop.tracer;
    };
    // By default does nothing
    Span.prototype._setOperationName = function (name) {
    };
    // By default does nothing
    Span.prototype._setBaggageItem = function (key, value) {
    };
    // By default does nothing
    Span.prototype._getBaggageItem = function (key) {
        return undefined;
    };
    // By default does nothing
    //
    // NOTE: both setTag() and addTags() map to this function. keyValuePairs
    // will always be an associative array.
    Span.prototype._addTags = function (keyValuePairs) {
    };
    // By default does nothing
    Span.prototype._log = function (keyValuePairs, timestamp) {
    };
    // By default does nothing
    //
    // finishTime is expected to be either a number or undefined.
    Span.prototype._finish = function (finishTime) {
    };
    return Span;
}());
exports.Span = Span;
exports.default = Span;
//# sourceMappingURL=span.js.map

/***/ }),

/***/ "../../node_modules/opentracing/lib/span_context.js":
/*!**********************************************************!*\
  !*** ../../node_modules/opentracing/lib/span_context.js ***!
  \**********************************************************/
/***/ (function(__unused_webpack_module, exports) {

"use strict";

Object.defineProperty(exports, "__esModule", ({ value: true }));
/**
 * SpanContext represents Span state that must propagate to descendant Spans
 * and across process boundaries.
 *
 * SpanContext is logically divided into two pieces: the user-level "Baggage"
 * (see setBaggageItem and getBaggageItem) that propagates across Span
 * boundaries and any Tracer-implementation-specific fields that are needed to
 * identify or otherwise contextualize the associated Span instance (e.g., a
 * <trace_id, span_id, sampled> tuple).
 */
var SpanContext = /** @class */ (function () {
    function SpanContext() {
    }
    return SpanContext;
}());
exports.SpanContext = SpanContext;
exports.default = SpanContext;
//# sourceMappingURL=span_context.js.map

/***/ }),

/***/ "../../node_modules/opentracing/lib/tracer.js":
/*!****************************************************!*\
  !*** ../../node_modules/opentracing/lib/tracer.js ***!
  \****************************************************/
/***/ (function(__unused_webpack_module, exports, __webpack_require__) {

"use strict";

Object.defineProperty(exports, "__esModule", ({ value: true }));
var Functions = __webpack_require__(/*! ./functions */ "../../node_modules/opentracing/lib/functions.js");
var Noop = __webpack_require__(/*! ./noop */ "../../node_modules/opentracing/lib/noop.js");
var span_1 = __webpack_require__(/*! ./span */ "../../node_modules/opentracing/lib/span.js");
/**
 * Tracer is the entry-point between the instrumentation API and the tracing
 * implementation.
 *
 * The default object acts as a no-op implementation.
 *
 * Note to implementators: derived classes can choose to directly implement the
 * methods in the "OpenTracing API methods" section, or optionally the subset of
 * underscore-prefixed methods to pick up the argument checking and handling
 * automatically from the base class.
 */
var Tracer = /** @class */ (function () {
    function Tracer() {
    }
    // ---------------------------------------------------------------------- //
    // OpenTracing API methods
    // ---------------------------------------------------------------------- //
    /**
     * Starts and returns a new Span representing a logical unit of work.
     *
     * For example:
     *
     *     // Start a new (parentless) root Span:
     *     var parent = Tracer.startSpan('DoWork');
     *
     *     // Start a new (child) Span:
     *     var child = Tracer.startSpan('load-from-db', {
     *         childOf: parent.context(),
     *     });
     *
     *     // Start a new async (FollowsFrom) Span:
     *     var child = Tracer.startSpan('async-cache-write', {
     *         references: [
     *             opentracing.followsFrom(parent.context())
     *         ],
     *     });
     *
     * @param {string} name - the name of the operation (REQUIRED).
     * @param {SpanOptions} [options] - options for the newly created span.
     * @return {Span} - a new Span object.
     */
    Tracer.prototype.startSpan = function (name, options) {
        if (options === void 0) { options = {}; }
        // Convert options.childOf to fields.references as needed.
        if (options.childOf) {
            // Convert from a Span or a SpanContext into a Reference.
            var childOf = Functions.childOf(options.childOf);
            if (options.references) {
                options.references.push(childOf);
            }
            else {
                options.references = [childOf];
            }
            delete (options.childOf);
        }
        return this._startSpan(name, options);
    };
    /**
     * Injects the given SpanContext instance for cross-process propagation
     * within `carrier`. The expected type of `carrier` depends on the value of
     * `format.
     *
     * OpenTracing defines a common set of `format` values (see
     * FORMAT_TEXT_MAP, FORMAT_HTTP_HEADERS, and FORMAT_BINARY), and each has
     * an expected carrier type.
     *
     * Consider this pseudocode example:
     *
     *     var clientSpan = ...;
     *     ...
     *     // Inject clientSpan into a text carrier.
     *     var headersCarrier = {};
     *     Tracer.inject(clientSpan.context(), Tracer.FORMAT_HTTP_HEADERS, headersCarrier);
     *     // Incorporate the textCarrier into the outbound HTTP request header
     *     // map.
     *     Object.assign(outboundHTTPReq.headers, headersCarrier);
     *     // ... send the httpReq
     *
     * @param  {SpanContext} spanContext - the SpanContext to inject into the
     *         carrier object. As a convenience, a Span instance may be passed
     *         in instead (in which case its .context() is used for the
     *         inject()).
     * @param  {string} format - the format of the carrier.
     * @param  {any} carrier - see the documentation for the chosen `format`
     *         for a description of the carrier object.
     */
    Tracer.prototype.inject = function (spanContext, format, carrier) {
        // Allow the user to pass a Span instead of a SpanContext
        if (spanContext instanceof span_1.default) {
            spanContext = spanContext.context();
        }
        return this._inject(spanContext, format, carrier);
    };
    /**
     * Returns a SpanContext instance extracted from `carrier` in the given
     * `format`.
     *
     * OpenTracing defines a common set of `format` values (see
     * FORMAT_TEXT_MAP, FORMAT_HTTP_HEADERS, and FORMAT_BINARY), and each has
     * an expected carrier type.
     *
     * Consider this pseudocode example:
     *
     *     // Use the inbound HTTP request's headers as a text map carrier.
     *     var headersCarrier = inboundHTTPReq.headers;
     *     var wireCtx = Tracer.extract(Tracer.FORMAT_HTTP_HEADERS, headersCarrier);
     *     var serverSpan = Tracer.startSpan('...', { childOf : wireCtx });
     *
     * @param  {string} format - the format of the carrier.
     * @param  {any} carrier - the type of the carrier object is determined by
     *         the format.
     * @return {SpanContext}
     *         The extracted SpanContext, or null if no such SpanContext could
     *         be found in `carrier`
     */
    Tracer.prototype.extract = function (format, carrier) {
        return this._extract(format, carrier);
    };
    // ---------------------------------------------------------------------- //
    // Derived classes can choose to implement the below
    // ---------------------------------------------------------------------- //
    // NOTE: the input to this method is *always* an associative array. The
    // public-facing startSpan() method normalizes the arguments so that
    // all N implementations do not need to worry about variations in the call
    // signature.
    //
    // The default behavior returns a no-op span.
    Tracer.prototype._startSpan = function (name, fields) {
        return Noop.span;
    };
    // The default behavior is a no-op.
    Tracer.prototype._inject = function (spanContext, format, carrier) {
    };
    // The default behavior is to return a no-op SpanContext.
    Tracer.prototype._extract = function (format, carrier) {
        return Noop.spanContext;
    };
    return Tracer;
}());
exports.Tracer = Tracer;
exports.default = Tracer;
//# sourceMappingURL=tracer.js.map

/***/ }),

/***/ "../../node_modules/promise-polyfill/src/finally.js":
/*!**********************************************************!*\
  !*** ../../node_modules/promise-polyfill/src/finally.js ***!
  \**********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/**
 * @this {Promise}
 */
function finallyConstructor(callback) {
  var constructor = this.constructor;
  return this.then(
    function(value) {
      // @ts-ignore
      return constructor.resolve(callback()).then(function() {
        return value;
      });
    },
    function(reason) {
      // @ts-ignore
      return constructor.resolve(callback()).then(function() {
        // @ts-ignore
        return constructor.reject(reason);
      });
    }
  );
}

/* harmony default export */ __webpack_exports__["default"] = (finallyConstructor);


/***/ }),

/***/ "../../node_modules/promise-polyfill/src/index.js":
/*!********************************************************!*\
  !*** ../../node_modules/promise-polyfill/src/index.js ***!
  \********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _finally__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./finally */ "../../node_modules/promise-polyfill/src/finally.js");


// Store setTimeout reference so promise-polyfill will be unaffected by
// other code modifying setTimeout (like sinon.useFakeTimers())
var setTimeoutFunc = setTimeout;

function isArray(x) {
  return Boolean(x && typeof x.length !== 'undefined');
}

function noop() {}

// Polyfill for Function.prototype.bind
function bind(fn, thisArg) {
  return function() {
    fn.apply(thisArg, arguments);
  };
}

/**
 * @constructor
 * @param {Function} fn
 */
function Promise(fn) {
  if (!(this instanceof Promise))
    throw new TypeError('Promises must be constructed via new');
  if (typeof fn !== 'function') throw new TypeError('not a function');
  /** @type {!number} */
  this._state = 0;
  /** @type {!boolean} */
  this._handled = false;
  /** @type {Promise|undefined} */
  this._value = undefined;
  /** @type {!Array<!Function>} */
  this._deferreds = [];

  doResolve(fn, this);
}

function handle(self, deferred) {
  while (self._state === 3) {
    self = self._value;
  }
  if (self._state === 0) {
    self._deferreds.push(deferred);
    return;
  }
  self._handled = true;
  Promise._immediateFn(function() {
    var cb = self._state === 1 ? deferred.onFulfilled : deferred.onRejected;
    if (cb === null) {
      (self._state === 1 ? resolve : reject)(deferred.promise, self._value);
      return;
    }
    var ret;
    try {
      ret = cb(self._value);
    } catch (e) {
      reject(deferred.promise, e);
      return;
    }
    resolve(deferred.promise, ret);
  });
}

function resolve(self, newValue) {
  try {
    // Promise Resolution Procedure: https://github.com/promises-aplus/promises-spec#the-promise-resolution-procedure
    if (newValue === self)
      throw new TypeError('A promise cannot be resolved with itself.');
    if (
      newValue &&
      (typeof newValue === 'object' || typeof newValue === 'function')
    ) {
      var then = newValue.then;
      if (newValue instanceof Promise) {
        self._state = 3;
        self._value = newValue;
        finale(self);
        return;
      } else if (typeof then === 'function') {
        doResolve(bind(then, newValue), self);
        return;
      }
    }
    self._state = 1;
    self._value = newValue;
    finale(self);
  } catch (e) {
    reject(self, e);
  }
}

function reject(self, newValue) {
  self._state = 2;
  self._value = newValue;
  finale(self);
}

function finale(self) {
  if (self._state === 2 && self._deferreds.length === 0) {
    Promise._immediateFn(function() {
      if (!self._handled) {
        Promise._unhandledRejectionFn(self._value);
      }
    });
  }

  for (var i = 0, len = self._deferreds.length; i < len; i++) {
    handle(self, self._deferreds[i]);
  }
  self._deferreds = null;
}

/**
 * @constructor
 */
function Handler(onFulfilled, onRejected, promise) {
  this.onFulfilled = typeof onFulfilled === 'function' ? onFulfilled : null;
  this.onRejected = typeof onRejected === 'function' ? onRejected : null;
  this.promise = promise;
}

/**
 * Take a potentially misbehaving resolver function and make sure
 * onFulfilled and onRejected are only called once.
 *
 * Makes no guarantees about asynchrony.
 */
function doResolve(fn, self) {
  var done = false;
  try {
    fn(
      function(value) {
        if (done) return;
        done = true;
        resolve(self, value);
      },
      function(reason) {
        if (done) return;
        done = true;
        reject(self, reason);
      }
    );
  } catch (ex) {
    if (done) return;
    done = true;
    reject(self, ex);
  }
}

Promise.prototype['catch'] = function(onRejected) {
  return this.then(null, onRejected);
};

Promise.prototype.then = function(onFulfilled, onRejected) {
  // @ts-ignore
  var prom = new this.constructor(noop);

  handle(this, new Handler(onFulfilled, onRejected, prom));
  return prom;
};

Promise.prototype['finally'] = _finally__WEBPACK_IMPORTED_MODULE_0__.default;

Promise.all = function(arr) {
  return new Promise(function(resolve, reject) {
    if (!isArray(arr)) {
      return reject(new TypeError('Promise.all accepts an array'));
    }

    var args = Array.prototype.slice.call(arr);
    if (args.length === 0) return resolve([]);
    var remaining = args.length;

    function res(i, val) {
      try {
        if (val && (typeof val === 'object' || typeof val === 'function')) {
          var then = val.then;
          if (typeof then === 'function') {
            then.call(
              val,
              function(val) {
                res(i, val);
              },
              reject
            );
            return;
          }
        }
        args[i] = val;
        if (--remaining === 0) {
          resolve(args);
        }
      } catch (ex) {
        reject(ex);
      }
    }

    for (var i = 0; i < args.length; i++) {
      res(i, args[i]);
    }
  });
};

Promise.resolve = function(value) {
  if (value && typeof value === 'object' && value.constructor === Promise) {
    return value;
  }

  return new Promise(function(resolve) {
    resolve(value);
  });
};

Promise.reject = function(value) {
  return new Promise(function(resolve, reject) {
    reject(value);
  });
};

Promise.race = function(arr) {
  return new Promise(function(resolve, reject) {
    if (!isArray(arr)) {
      return reject(new TypeError('Promise.race accepts an array'));
    }

    for (var i = 0, len = arr.length; i < len; i++) {
      Promise.resolve(arr[i]).then(resolve, reject);
    }
  });
};

// Use polyfill for setImmediate for performance gains
Promise._immediateFn =
  // @ts-ignore
  (typeof setImmediate === 'function' &&
    function(fn) {
      // @ts-ignore
      setImmediate(fn);
    }) ||
  function(fn) {
    setTimeoutFunc(fn, 0);
  };

Promise._unhandledRejectionFn = function _unhandledRejectionFn(err) {
  if (typeof console !== 'undefined' && console) {
    console.warn('Possible Unhandled Promise Rejection:', err); // eslint-disable-line no-console
  }
};

/* harmony default export */ __webpack_exports__["default"] = (Promise);


/***/ }),

/***/ "../../node_modules/stackframe/stackframe.js":
/*!***************************************************!*\
  !*** ../../node_modules/stackframe/stackframe.js ***!
  \***************************************************/
/***/ (function(module, exports) {

var __WEBPACK_AMD_DEFINE_FACTORY__, __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;(function (root, factory) {
    'use strict';
    // Universal Module Definition (UMD) to support AMD, CommonJS/Node.js, Rhino, and browsers.

    /* istanbul ignore next */
    if (true) {
        !(__WEBPACK_AMD_DEFINE_ARRAY__ = [], __WEBPACK_AMD_DEFINE_FACTORY__ = (factory),
		__WEBPACK_AMD_DEFINE_RESULT__ = (typeof __WEBPACK_AMD_DEFINE_FACTORY__ === 'function' ?
		(__WEBPACK_AMD_DEFINE_FACTORY__.apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__)) : __WEBPACK_AMD_DEFINE_FACTORY__),
		__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
    } else {}
}(this, function () {
    'use strict';
    function _isNumber(n) {
        return !isNaN(parseFloat(n)) && isFinite(n);
    }

    function StackFrame(functionName, args, fileName, lineNumber, columnNumber, source) {
        if (functionName !== undefined) {
            this.setFunctionName(functionName);
        }
        if (args !== undefined) {
            this.setArgs(args);
        }
        if (fileName !== undefined) {
            this.setFileName(fileName);
        }
        if (lineNumber !== undefined) {
            this.setLineNumber(lineNumber);
        }
        if (columnNumber !== undefined) {
            this.setColumnNumber(columnNumber);
        }
        if (source !== undefined) {
            this.setSource(source);
        }
    }

    StackFrame.prototype = {
        getFunctionName: function () {
            return this.functionName;
        },
        setFunctionName: function (v) {
            this.functionName = String(v);
        },

        getArgs: function () {
            return this.args;
        },
        setArgs: function (v) {
            if (Object.prototype.toString.call(v) !== '[object Array]') {
                throw new TypeError('Args must be an Array');
            }
            this.args = v;
        },

        // NOTE: Property name may be misleading as it includes the path,
        // but it somewhat mirrors V8's JavaScriptStackTraceApi
        // https://code.google.com/p/v8/wiki/JavaScriptStackTraceApi and Gecko's
        // http://mxr.mozilla.org/mozilla-central/source/xpcom/base/nsIException.idl#14
        getFileName: function () {
            return this.fileName;
        },
        setFileName: function (v) {
            this.fileName = String(v);
        },

        getLineNumber: function () {
            return this.lineNumber;
        },
        setLineNumber: function (v) {
            if (!_isNumber(v)) {
                throw new TypeError('Line Number must be a Number');
            }
            this.lineNumber = Number(v);
        },

        getColumnNumber: function () {
            return this.columnNumber;
        },
        setColumnNumber: function (v) {
            if (!_isNumber(v)) {
                throw new TypeError('Column Number must be a Number');
            }
            this.columnNumber = Number(v);
        },

        getSource: function () {
            return this.source;
        },
        setSource: function (v) {
            this.source = String(v);
        },

        toString: function() {
            var functionName = this.getFunctionName() || '{anonymous}';
            var args = '(' + (this.getArgs() || []).join(',') + ')';
            var fileName = this.getFileName() ? ('@' + this.getFileName()) : '';
            var lineNumber = _isNumber(this.getLineNumber()) ? (':' + this.getLineNumber()) : '';
            var columnNumber = _isNumber(this.getColumnNumber()) ? (':' + this.getColumnNumber()) : '';
            return functionName + args + fileName + lineNumber + columnNumber;
        }
    };

    return StackFrame;
}));


/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/compat get default export */
/******/ 	!function() {
/******/ 		// getDefaultExport function for compatibility with non-harmony modules
/******/ 		__webpack_require__.n = function(module) {
/******/ 			var getter = module && module.__esModule ?
/******/ 				function() { return module['default']; } :
/******/ 				function() { return module; };
/******/ 			__webpack_require__.d(getter, { a: getter });
/******/ 			return getter;
/******/ 		};
/******/ 	}();
/******/ 	
/******/ 	/* webpack/runtime/define property getters */
/******/ 	!function() {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = function(exports, definition) {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	}();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	!function() {
/******/ 		__webpack_require__.o = function(obj, prop) { return Object.prototype.hasOwnProperty.call(obj, prop); }
/******/ 	}();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	!function() {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = function(exports) {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	}();
/******/ 	
/************************************************************************/
var __webpack_exports__ = {};
// This entry need to be wrapped in an IIFE because it need to be in strict mode.
!function() {
"use strict";
/*!**********************!*\
  !*** ./src/index.js ***!
  \**********************/
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "init": function() { return /* binding */ init; },
/* harmony export */   "apmBase": function() { return /* binding */ apmBase; },
/* harmony export */   "ApmBase": function() { return /* reexport safe */ _apm_base__WEBPACK_IMPORTED_MODULE_0__.default; },
/* harmony export */   "apm": function() { return /* binding */ apmBase; }
/* harmony export */ });
/* harmony import */ var _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @elastic/apm-rum-core */ "../rum-core/dist/es/common/utils.js");
/* harmony import */ var _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! @elastic/apm-rum-core */ "../rum-core/dist/es/bootstrap.js");
/* harmony import */ var _elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! @elastic/apm-rum-core */ "../rum-core/dist/es/index.js");
/* harmony import */ var _apm_base__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./apm-base */ "./src/apm-base.js");



function getApmBase() {
  if (_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_1__.isBrowser && window.elasticApm) {
    return window.elasticApm;
  }

  var enabled = (0,_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_2__.bootstrap)();
  var serviceFactory = (0,_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_3__.createServiceFactory)();
  var apmBase = new _apm_base__WEBPACK_IMPORTED_MODULE_0__.default(serviceFactory, !enabled);

  if (_elastic_apm_rum_core__WEBPACK_IMPORTED_MODULE_1__.isBrowser) {
    window.elasticApm = apmBase;
  }

  return apmBase;
}

var apmBase = getApmBase();
var init = apmBase.init.bind(apmBase);
/* harmony default export */ __webpack_exports__["default"] = (init);

}();
/******/ 	return __webpack_exports__;
/******/ })()
;
});
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZWxhc3RpYy1hcG0tcnVtLnVtZC5qcyIsInNvdXJjZXMiOlsid2VicGFjazovL1tuYW1lXS93ZWJwYWNrL3VuaXZlcnNhbE1vZHVsZURlZmluaXRpb24iLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvYm9vdHN0cmFwLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2NvbW1vbi9hZnRlci1mcmFtZS5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9jb21tb24vYXBtLXNlcnZlci5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9jb21tb24vY29tcHJlc3MuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL2NvbmZpZy1zZXJ2aWNlLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2NvbW1vbi9jb25zdGFudHMuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL2NvbnRleHQuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL2V2ZW50LWhhbmRsZXIuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL2h0dHAvZmV0Y2guanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL2h0dHAvcmVzcG9uc2Utc3RhdHVzLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2NvbW1vbi9odHRwL3hoci5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9jb21tb24vaW5zdHJ1bWVudC5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9jb21tb24vbG9nZ2luZy1zZXJ2aWNlLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2NvbW1vbi9uZGpzb24uanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL29ic2VydmVycy9wYWdlLWNsaWNrcy5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9jb21tb24vb2JzZXJ2ZXJzL3BhZ2UtdmlzaWJpbGl0eS5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9jb21tb24vcGF0Y2hpbmcvZmV0Y2gtcGF0Y2guanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL3BhdGNoaW5nL2hpc3RvcnktcGF0Y2guanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL3BhdGNoaW5nL2luZGV4LmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2NvbW1vbi9wYXRjaGluZy9wYXRjaC11dGlscy5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9jb21tb24vcGF0Y2hpbmcveGhyLXBhdGNoLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2NvbW1vbi9wb2x5ZmlsbHMuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL3F1ZXVlLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2NvbW1vbi9zZXJ2aWNlLWZhY3RvcnkuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvY29tbW9uL3Rocm90dGxlLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2NvbW1vbi90cnVuY2F0ZS5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9jb21tb24vdXJsLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2NvbW1vbi91dGlscy5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9lcnJvci1sb2dnaW5nL2Vycm9yLWxvZ2dpbmcuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvZXJyb3ItbG9nZ2luZy9pbmRleC5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9lcnJvci1sb2dnaW5nL3N0YWNrLXRyYWNlLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL2luZGV4LmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL29wZW50cmFjaW5nL2luZGV4LmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL29wZW50cmFjaW5nL3NwYW4uanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvb3BlbnRyYWNpbmcvdHJhY2VyLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL3BlcmZvcm1hbmNlLW1vbml0b3JpbmcvYnJlYWtkb3duLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL3BlcmZvcm1hbmNlLW1vbml0b3JpbmcvY2FwdHVyZS1uYXZpZ2F0aW9uLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL3BlcmZvcm1hbmNlLW1vbml0b3JpbmcvaW5kZXguanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvcGVyZm9ybWFuY2UtbW9uaXRvcmluZy9tZXRyaWNzLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL3BlcmZvcm1hbmNlLW1vbml0b3JpbmcvcGVyZm9ybWFuY2UtbW9uaXRvcmluZy5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9wZXJmb3JtYW5jZS1tb25pdG9yaW5nL3NwYW4tYmFzZS5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vcnVtLWNvcmUvZGlzdC9lcy9wZXJmb3JtYW5jZS1tb25pdG9yaW5nL3NwYW4uanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvcGVyZm9ybWFuY2UtbW9uaXRvcmluZy90cmFuc2FjdGlvbi1zZXJ2aWNlLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi9ydW0tY29yZS9kaXN0L2VzL3BlcmZvcm1hbmNlLW1vbml0b3JpbmcvdHJhbnNhY3Rpb24uanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uL3J1bS1jb3JlL2Rpc3QvZXMvc3RhdGUuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4vc3JjL2FwbS1iYXNlLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi8uLi9ub2RlX21vZHVsZXMvZXJyb3Itc3RhY2stcGFyc2VyL2Vycm9yLXN0YWNrLXBhcnNlci5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vLi4vbm9kZV9tb2R1bGVzL29wZW50cmFjaW5nL2xpYi9jb25zdGFudHMuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uLy4uL25vZGVfbW9kdWxlcy9vcGVudHJhY2luZy9saWIvZnVuY3Rpb25zLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi8uLi9ub2RlX21vZHVsZXMvb3BlbnRyYWNpbmcvbGliL25vb3AuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uLy4uL25vZGVfbW9kdWxlcy9vcGVudHJhY2luZy9saWIvcmVmZXJlbmNlLmpzIiwid2VicGFjazovL1tuYW1lXS8uLi8uLi9ub2RlX21vZHVsZXMvb3BlbnRyYWNpbmcvbGliL3NwYW4uanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uLy4uL25vZGVfbW9kdWxlcy9vcGVudHJhY2luZy9saWIvc3Bhbl9jb250ZXh0LmpzIiwid2VicGFjazovL1tuYW1lXS8uLi8uLi9ub2RlX21vZHVsZXMvb3BlbnRyYWNpbmcvbGliL3RyYWNlci5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vLi4vbm9kZV9tb2R1bGVzL3Byb21pc2UtcG9seWZpbGwvc3JjL2ZpbmFsbHkuanMiLCJ3ZWJwYWNrOi8vW25hbWVdLy4uLy4uL25vZGVfbW9kdWxlcy9wcm9taXNlLXBvbHlmaWxsL3NyYy9pbmRleC5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vLi4vLi4vbm9kZV9tb2R1bGVzL3N0YWNrZnJhbWUvc3RhY2tmcmFtZS5qcyIsIndlYnBhY2s6Ly9bbmFtZV0vd2VicGFjay9ib290c3RyYXAiLCJ3ZWJwYWNrOi8vW25hbWVdL3dlYnBhY2svcnVudGltZS9jb21wYXQgZ2V0IGRlZmF1bHQgZXhwb3J0Iiwid2VicGFjazovL1tuYW1lXS93ZWJwYWNrL3J1bnRpbWUvZGVmaW5lIHByb3BlcnR5IGdldHRlcnMiLCJ3ZWJwYWNrOi8vW25hbWVdL3dlYnBhY2svcnVudGltZS9oYXNPd25Qcm9wZXJ0eSBzaG9ydGhhbmQiLCJ3ZWJwYWNrOi8vW25hbWVdL3dlYnBhY2svcnVudGltZS9tYWtlIG5hbWVzcGFjZSBvYmplY3QiLCJ3ZWJwYWNrOi8vW25hbWVdLy4vc3JjL2luZGV4LmpzIl0sInNvdXJjZXNDb250ZW50IjpbIihmdW5jdGlvbiB3ZWJwYWNrVW5pdmVyc2FsTW9kdWxlRGVmaW5pdGlvbihyb290LCBmYWN0b3J5KSB7XG5cdGlmKHR5cGVvZiBleHBvcnRzID09PSAnb2JqZWN0JyAmJiB0eXBlb2YgbW9kdWxlID09PSAnb2JqZWN0Jylcblx0XHRtb2R1bGUuZXhwb3J0cyA9IGZhY3RvcnkoKTtcblx0ZWxzZSBpZih0eXBlb2YgZGVmaW5lID09PSAnZnVuY3Rpb24nICYmIGRlZmluZS5hbWQpXG5cdFx0ZGVmaW5lKFtdLCBmYWN0b3J5KTtcblx0ZWxzZSBpZih0eXBlb2YgZXhwb3J0cyA9PT0gJ29iamVjdCcpXG5cdFx0ZXhwb3J0c1tcImVsYXN0aWMtYXBtLXJ1bVwiXSA9IGZhY3RvcnkoKTtcblx0ZWxzZVxuXHRcdHJvb3RbXCJlbGFzdGljLWFwbS1ydW1cIl0gPSBmYWN0b3J5KCk7XG59KShzZWxmLCBmdW5jdGlvbigpIHtcbnJldHVybiAiLCJpbXBvcnQgeyBpc1BsYXRmb3JtU3VwcG9ydGVkLCBpc0Jyb3dzZXIsIG5vdyB9IGZyb20gJy4vY29tbW9uL3V0aWxzJztcbmltcG9ydCB7IHBhdGNoQWxsIH0gZnJvbSAnLi9jb21tb24vcGF0Y2hpbmcnO1xuaW1wb3J0IHsgc3RhdGUgfSBmcm9tICcuL3N0YXRlJztcbnZhciBlbmFibGVkID0gZmFsc2U7XG5leHBvcnQgZnVuY3Rpb24gYm9vdHN0cmFwKCkge1xuICBpZiAoaXNQbGF0Zm9ybVN1cHBvcnRlZCgpKSB7XG4gICAgcGF0Y2hBbGwoKTtcbiAgICBzdGF0ZS5ib290c3RyYXBUaW1lID0gbm93KCk7XG4gICAgZW5hYmxlZCA9IHRydWU7XG4gIH0gZWxzZSBpZiAoaXNCcm93c2VyKSB7XG4gICAgY29uc29sZS5sb2coJ1tFbGFzdGljIEFQTV0gcGxhdGZvcm0gaXMgbm90IHN1cHBvcnRlZCEnKTtcbiAgfVxuXG4gIHJldHVybiBlbmFibGVkO1xufSIsInZhciBSQUZfVElNRU9VVCA9IDEwMDtcbmV4cG9ydCBkZWZhdWx0IGZ1bmN0aW9uIGFmdGVyRnJhbWUoY2FsbGJhY2spIHtcbiAgdmFyIGhhbmRsZXIgPSBmdW5jdGlvbiBoYW5kbGVyKCkge1xuICAgIGNsZWFyVGltZW91dCh0aW1lb3V0KTtcbiAgICBjYW5jZWxBbmltYXRpb25GcmFtZShyYWYpO1xuICAgIHNldFRpbWVvdXQoY2FsbGJhY2spO1xuICB9O1xuXG4gIHZhciB0aW1lb3V0ID0gc2V0VGltZW91dChoYW5kbGVyLCBSQUZfVElNRU9VVCk7XG4gIHZhciByYWYgPSByZXF1ZXN0QW5pbWF0aW9uRnJhbWUoaGFuZGxlcik7XG59IiwiaW1wb3J0IFF1ZXVlIGZyb20gJy4vcXVldWUnO1xuaW1wb3J0IHRocm90dGxlIGZyb20gJy4vdGhyb3R0bGUnO1xuaW1wb3J0IE5ESlNPTiBmcm9tICcuL25kanNvbic7XG5pbXBvcnQgeyB0cnVuY2F0ZU1vZGVsLCBNRVRBREFUQV9NT0RFTCB9IGZyb20gJy4vdHJ1bmNhdGUnO1xuaW1wb3J0IHsgRVJST1JTLCBIVFRQX1JFUVVFU1RfVElNRU9VVCwgUVVFVUVfRkxVU0gsIFRSQU5TQUNUSU9OUyB9IGZyb20gJy4vY29uc3RhbnRzJztcbmltcG9ydCB7IG5vb3AgfSBmcm9tICcuL3V0aWxzJztcbmltcG9ydCB7IFByb21pc2UgfSBmcm9tICcuL3BvbHlmaWxscyc7XG5pbXBvcnQgeyBjb21wcmVzc01ldGFkYXRhLCBjb21wcmVzc1RyYW5zYWN0aW9uLCBjb21wcmVzc0Vycm9yLCBjb21wcmVzc1BheWxvYWQgfSBmcm9tICcuL2NvbXByZXNzJztcbmltcG9ydCB7IF9fREVWX18gfSBmcm9tICcuLi9zdGF0ZSc7XG5pbXBvcnQgeyBzZW5kRmV0Y2hSZXF1ZXN0LCBzaG91bGRVc2VGZXRjaFdpdGhLZWVwQWxpdmUgfSBmcm9tICcuL2h0dHAvZmV0Y2gnO1xuaW1wb3J0IHsgc2VuZFhIUiB9IGZyb20gJy4vaHR0cC94aHInO1xudmFyIFRIUk9UVExFX0lOVEVSVkFMID0gNjAwMDA7XG5cbnZhciBBcG1TZXJ2ZXIgPSBmdW5jdGlvbiAoKSB7XG4gIGZ1bmN0aW9uIEFwbVNlcnZlcihjb25maWdTZXJ2aWNlLCBsb2dnaW5nU2VydmljZSkge1xuICAgIHRoaXMuX2NvbmZpZ1NlcnZpY2UgPSBjb25maWdTZXJ2aWNlO1xuICAgIHRoaXMuX2xvZ2dpbmdTZXJ2aWNlID0gbG9nZ2luZ1NlcnZpY2U7XG4gICAgdGhpcy5xdWV1ZSA9IHVuZGVmaW5lZDtcbiAgICB0aGlzLnRocm90dGxlRXZlbnRzID0gbm9vcDtcbiAgfVxuXG4gIHZhciBfcHJvdG8gPSBBcG1TZXJ2ZXIucHJvdG90eXBlO1xuXG4gIF9wcm90by5pbml0ID0gZnVuY3Rpb24gaW5pdCgpIHtcbiAgICB2YXIgX3RoaXMgPSB0aGlzO1xuXG4gICAgdmFyIHF1ZXVlTGltaXQgPSB0aGlzLl9jb25maWdTZXJ2aWNlLmdldCgncXVldWVMaW1pdCcpO1xuXG4gICAgdmFyIGZsdXNoSW50ZXJ2YWwgPSB0aGlzLl9jb25maWdTZXJ2aWNlLmdldCgnZmx1c2hJbnRlcnZhbCcpO1xuXG4gICAgdmFyIGxpbWl0ID0gdGhpcy5fY29uZmlnU2VydmljZS5nZXQoJ2V2ZW50c0xpbWl0Jyk7XG5cbiAgICB2YXIgb25GbHVzaCA9IGZ1bmN0aW9uIG9uRmx1c2goZXZlbnRzKSB7XG4gICAgICB2YXIgcHJvbWlzZSA9IF90aGlzLnNlbmRFdmVudHMoZXZlbnRzKTtcblxuICAgICAgaWYgKHByb21pc2UpIHtcbiAgICAgICAgcHJvbWlzZS5jYXRjaChmdW5jdGlvbiAocmVhc29uKSB7XG4gICAgICAgICAgX3RoaXMuX2xvZ2dpbmdTZXJ2aWNlLndhcm4oJ0ZhaWxlZCBzZW5kaW5nIGV2ZW50cyEnLCBfdGhpcy5fY29uc3RydWN0RXJyb3IocmVhc29uKSk7XG4gICAgICAgIH0pO1xuICAgICAgfVxuICAgIH07XG5cbiAgICB0aGlzLnF1ZXVlID0gbmV3IFF1ZXVlKG9uRmx1c2gsIHtcbiAgICAgIHF1ZXVlTGltaXQ6IHF1ZXVlTGltaXQsXG4gICAgICBmbHVzaEludGVydmFsOiBmbHVzaEludGVydmFsXG4gICAgfSk7XG4gICAgdGhpcy50aHJvdHRsZUV2ZW50cyA9IHRocm90dGxlKHRoaXMucXVldWUuYWRkLmJpbmQodGhpcy5xdWV1ZSksIGZ1bmN0aW9uICgpIHtcbiAgICAgIHJldHVybiBfdGhpcy5fbG9nZ2luZ1NlcnZpY2Uud2FybignRHJvcHBlZCBldmVudHMgZHVlIHRvIHRocm90dGxpbmchJyk7XG4gICAgfSwge1xuICAgICAgbGltaXQ6IGxpbWl0LFxuICAgICAgaW50ZXJ2YWw6IFRIUk9UVExFX0lOVEVSVkFMXG4gICAgfSk7XG5cbiAgICB0aGlzLl9jb25maWdTZXJ2aWNlLm9ic2VydmVFdmVudChRVUVVRV9GTFVTSCwgZnVuY3Rpb24gKCkge1xuICAgICAgX3RoaXMucXVldWUuZmx1c2goKTtcbiAgICB9KTtcbiAgfTtcblxuICBfcHJvdG8uX3Bvc3RKc29uID0gZnVuY3Rpb24gX3Bvc3RKc29uKGVuZFBvaW50LCBwYXlsb2FkKSB7XG4gICAgdmFyIF90aGlzMiA9IHRoaXM7XG5cbiAgICB2YXIgaGVhZGVycyA9IHtcbiAgICAgICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24veC1uZGpzb24nXG4gICAgfTtcblxuICAgIHZhciBhcG1SZXF1ZXN0ID0gdGhpcy5fY29uZmlnU2VydmljZS5nZXQoJ2FwbVJlcXVlc3QnKTtcblxuICAgIHZhciBwYXJhbXMgPSB7XG4gICAgICBwYXlsb2FkOiBwYXlsb2FkLFxuICAgICAgaGVhZGVyczogaGVhZGVycyxcbiAgICAgIGJlZm9yZVNlbmQ6IGFwbVJlcXVlc3RcbiAgICB9O1xuICAgIHJldHVybiBjb21wcmVzc1BheWxvYWQocGFyYW1zKS5jYXRjaChmdW5jdGlvbiAoZXJyb3IpIHtcbiAgICAgIGlmIChfX0RFVl9fKSB7XG4gICAgICAgIF90aGlzMi5fbG9nZ2luZ1NlcnZpY2UuZGVidWcoJ0NvbXByZXNzaW5nIHRoZSBwYXlsb2FkIHVzaW5nIENvbXByZXNzaW9uU3RyZWFtIEFQSSBmYWlsZWQnLCBlcnJvci5tZXNzYWdlKTtcbiAgICAgIH1cblxuICAgICAgcmV0dXJuIHBhcmFtcztcbiAgICB9KS50aGVuKGZ1bmN0aW9uIChyZXN1bHQpIHtcbiAgICAgIHJldHVybiBfdGhpczIuX21ha2VIdHRwUmVxdWVzdCgnUE9TVCcsIGVuZFBvaW50LCByZXN1bHQpO1xuICAgIH0pLnRoZW4oZnVuY3Rpb24gKF9yZWYpIHtcbiAgICAgIHZhciByZXNwb25zZVRleHQgPSBfcmVmLnJlc3BvbnNlVGV4dDtcbiAgICAgIHJldHVybiByZXNwb25zZVRleHQ7XG4gICAgfSk7XG4gIH07XG5cbiAgX3Byb3RvLl9jb25zdHJ1Y3RFcnJvciA9IGZ1bmN0aW9uIF9jb25zdHJ1Y3RFcnJvcihyZWFzb24pIHtcbiAgICB2YXIgdXJsID0gcmVhc29uLnVybCxcbiAgICAgICAgc3RhdHVzID0gcmVhc29uLnN0YXR1cyxcbiAgICAgICAgcmVzcG9uc2VUZXh0ID0gcmVhc29uLnJlc3BvbnNlVGV4dDtcblxuICAgIGlmICh0eXBlb2Ygc3RhdHVzID09ICd1bmRlZmluZWQnKSB7XG4gICAgICByZXR1cm4gcmVhc29uO1xuICAgIH1cblxuICAgIHZhciBtZXNzYWdlID0gdXJsICsgJyBIVFRQIHN0YXR1czogJyArIHN0YXR1cztcblxuICAgIGlmIChfX0RFVl9fICYmIHJlc3BvbnNlVGV4dCkge1xuICAgICAgdHJ5IHtcbiAgICAgICAgdmFyIHNlcnZlckVycm9ycyA9IFtdO1xuICAgICAgICB2YXIgcmVzcG9uc2UgPSBKU09OLnBhcnNlKHJlc3BvbnNlVGV4dCk7XG5cbiAgICAgICAgaWYgKHJlc3BvbnNlLmVycm9ycyAmJiByZXNwb25zZS5lcnJvcnMubGVuZ3RoID4gMCkge1xuICAgICAgICAgIHJlc3BvbnNlLmVycm9ycy5mb3JFYWNoKGZ1bmN0aW9uIChlcnIpIHtcbiAgICAgICAgICAgIHJldHVybiBzZXJ2ZXJFcnJvcnMucHVzaChlcnIubWVzc2FnZSk7XG4gICAgICAgICAgfSk7XG4gICAgICAgICAgbWVzc2FnZSArPSAnICcgKyBzZXJ2ZXJFcnJvcnMuam9pbignLCcpO1xuICAgICAgICB9XG4gICAgICB9IGNhdGNoIChlKSB7XG4gICAgICAgIHRoaXMuX2xvZ2dpbmdTZXJ2aWNlLmRlYnVnKCdFcnJvciBwYXJzaW5nIHJlc3BvbnNlIGZyb20gQVBNIHNlcnZlcicsIGUpO1xuICAgICAgfVxuICAgIH1cblxuICAgIHJldHVybiBuZXcgRXJyb3IobWVzc2FnZSk7XG4gIH07XG5cbiAgX3Byb3RvLl9tYWtlSHR0cFJlcXVlc3QgPSBmdW5jdGlvbiBfbWFrZUh0dHBSZXF1ZXN0KG1ldGhvZCwgdXJsLCBfdGVtcCkge1xuICAgIHZhciBfcmVmMiA9IF90ZW1wID09PSB2b2lkIDAgPyB7fSA6IF90ZW1wLFxuICAgICAgICBfcmVmMiR0aW1lb3V0ID0gX3JlZjIudGltZW91dCxcbiAgICAgICAgdGltZW91dCA9IF9yZWYyJHRpbWVvdXQgPT09IHZvaWQgMCA/IEhUVFBfUkVRVUVTVF9USU1FT1VUIDogX3JlZjIkdGltZW91dCxcbiAgICAgICAgcGF5bG9hZCA9IF9yZWYyLnBheWxvYWQsXG4gICAgICAgIGhlYWRlcnMgPSBfcmVmMi5oZWFkZXJzLFxuICAgICAgICBiZWZvcmVTZW5kID0gX3JlZjIuYmVmb3JlU2VuZDtcblxuICAgIHZhciBzZW5kQ3JlZGVudGlhbHMgPSB0aGlzLl9jb25maWdTZXJ2aWNlLmdldCgnc2VuZENyZWRlbnRpYWxzJyk7XG5cbiAgICBpZiAoIWJlZm9yZVNlbmQgJiYgc2hvdWxkVXNlRmV0Y2hXaXRoS2VlcEFsaXZlKG1ldGhvZCwgcGF5bG9hZCkpIHtcbiAgICAgIHJldHVybiBzZW5kRmV0Y2hSZXF1ZXN0KG1ldGhvZCwgdXJsLCB7XG4gICAgICAgIGtlZXBhbGl2ZTogdHJ1ZSxcbiAgICAgICAgdGltZW91dDogdGltZW91dCxcbiAgICAgICAgcGF5bG9hZDogcGF5bG9hZCxcbiAgICAgICAgaGVhZGVyczogaGVhZGVycyxcbiAgICAgICAgc2VuZENyZWRlbnRpYWxzOiBzZW5kQ3JlZGVudGlhbHNcbiAgICAgIH0pLmNhdGNoKGZ1bmN0aW9uIChyZWFzb24pIHtcbiAgICAgICAgaWYgKHJlYXNvbiBpbnN0YW5jZW9mIFR5cGVFcnJvcikge1xuICAgICAgICAgIHJldHVybiBzZW5kWEhSKG1ldGhvZCwgdXJsLCB7XG4gICAgICAgICAgICB0aW1lb3V0OiB0aW1lb3V0LFxuICAgICAgICAgICAgcGF5bG9hZDogcGF5bG9hZCxcbiAgICAgICAgICAgIGhlYWRlcnM6IGhlYWRlcnMsXG4gICAgICAgICAgICBiZWZvcmVTZW5kOiBiZWZvcmVTZW5kLFxuICAgICAgICAgICAgc2VuZENyZWRlbnRpYWxzOiBzZW5kQ3JlZGVudGlhbHNcbiAgICAgICAgICB9KTtcbiAgICAgICAgfVxuXG4gICAgICAgIHRocm93IHJlYXNvbjtcbiAgICAgIH0pO1xuICAgIH1cblxuICAgIHJldHVybiBzZW5kWEhSKG1ldGhvZCwgdXJsLCB7XG4gICAgICB0aW1lb3V0OiB0aW1lb3V0LFxuICAgICAgcGF5bG9hZDogcGF5bG9hZCxcbiAgICAgIGhlYWRlcnM6IGhlYWRlcnMsXG4gICAgICBiZWZvcmVTZW5kOiBiZWZvcmVTZW5kLFxuICAgICAgc2VuZENyZWRlbnRpYWxzOiBzZW5kQ3JlZGVudGlhbHNcbiAgICB9KTtcbiAgfTtcblxuICBfcHJvdG8uZmV0Y2hDb25maWcgPSBmdW5jdGlvbiBmZXRjaENvbmZpZyhzZXJ2aWNlTmFtZSwgZW52aXJvbm1lbnQpIHtcbiAgICB2YXIgX3RoaXMzID0gdGhpcztcblxuICAgIHZhciBfdGhpcyRnZXRFbmRwb2ludHMgPSB0aGlzLmdldEVuZHBvaW50cygpLFxuICAgICAgICBjb25maWdFbmRwb2ludCA9IF90aGlzJGdldEVuZHBvaW50cy5jb25maWdFbmRwb2ludDtcblxuICAgIGlmICghc2VydmljZU5hbWUpIHtcbiAgICAgIHJldHVybiBQcm9taXNlLnJlamVjdCgnc2VydmljZU5hbWUgaXMgcmVxdWlyZWQgZm9yIGZldGNoaW5nIGNlbnRyYWwgY29uZmlnLicpO1xuICAgIH1cblxuICAgIGNvbmZpZ0VuZHBvaW50ICs9IFwiP3NlcnZpY2UubmFtZT1cIiArIHNlcnZpY2VOYW1lO1xuXG4gICAgaWYgKGVudmlyb25tZW50KSB7XG4gICAgICBjb25maWdFbmRwb2ludCArPSBcIiZzZXJ2aWNlLmVudmlyb25tZW50PVwiICsgZW52aXJvbm1lbnQ7XG4gICAgfVxuXG4gICAgdmFyIGxvY2FsQ29uZmlnID0gdGhpcy5fY29uZmlnU2VydmljZS5nZXRMb2NhbENvbmZpZygpO1xuXG4gICAgaWYgKGxvY2FsQ29uZmlnKSB7XG4gICAgICBjb25maWdFbmRwb2ludCArPSBcIiZpZm5vbmVtYXRjaD1cIiArIGxvY2FsQ29uZmlnLmV0YWc7XG4gICAgfVxuXG4gICAgdmFyIGFwbVJlcXVlc3QgPSB0aGlzLl9jb25maWdTZXJ2aWNlLmdldCgnYXBtUmVxdWVzdCcpO1xuXG4gICAgcmV0dXJuIHRoaXMuX21ha2VIdHRwUmVxdWVzdCgnR0VUJywgY29uZmlnRW5kcG9pbnQsIHtcbiAgICAgIHRpbWVvdXQ6IDUwMDAsXG4gICAgICBiZWZvcmVTZW5kOiBhcG1SZXF1ZXN0XG4gICAgfSkudGhlbihmdW5jdGlvbiAoeGhyKSB7XG4gICAgICB2YXIgc3RhdHVzID0geGhyLnN0YXR1cyxcbiAgICAgICAgICByZXNwb25zZVRleHQgPSB4aHIucmVzcG9uc2VUZXh0O1xuXG4gICAgICBpZiAoc3RhdHVzID09PSAzMDQpIHtcbiAgICAgICAgcmV0dXJuIGxvY2FsQ29uZmlnO1xuICAgICAgfSBlbHNlIHtcbiAgICAgICAgdmFyIHJlbW90ZUNvbmZpZyA9IEpTT04ucGFyc2UocmVzcG9uc2VUZXh0KTtcbiAgICAgICAgdmFyIGV0YWcgPSB4aHIuZ2V0UmVzcG9uc2VIZWFkZXIoJ2V0YWcnKTtcblxuICAgICAgICBpZiAoZXRhZykge1xuICAgICAgICAgIHJlbW90ZUNvbmZpZy5ldGFnID0gZXRhZy5yZXBsYWNlKC9bXCJdL2csICcnKTtcblxuICAgICAgICAgIF90aGlzMy5fY29uZmlnU2VydmljZS5zZXRMb2NhbENvbmZpZyhyZW1vdGVDb25maWcsIHRydWUpO1xuICAgICAgICB9XG5cbiAgICAgICAgcmV0dXJuIHJlbW90ZUNvbmZpZztcbiAgICAgIH1cbiAgICB9KS5jYXRjaChmdW5jdGlvbiAocmVhc29uKSB7XG4gICAgICB2YXIgZXJyb3IgPSBfdGhpczMuX2NvbnN0cnVjdEVycm9yKHJlYXNvbik7XG5cbiAgICAgIHJldHVybiBQcm9taXNlLnJlamVjdChlcnJvcik7XG4gICAgfSk7XG4gIH07XG5cbiAgX3Byb3RvLmNyZWF0ZU1ldGFEYXRhID0gZnVuY3Rpb24gY3JlYXRlTWV0YURhdGEoKSB7XG4gICAgdmFyIGNmZyA9IHRoaXMuX2NvbmZpZ1NlcnZpY2U7XG4gICAgdmFyIG1ldGFkYXRhID0ge1xuICAgICAgc2VydmljZToge1xuICAgICAgICBuYW1lOiBjZmcuZ2V0KCdzZXJ2aWNlTmFtZScpLFxuICAgICAgICB2ZXJzaW9uOiBjZmcuZ2V0KCdzZXJ2aWNlVmVyc2lvbicpLFxuICAgICAgICBhZ2VudDoge1xuICAgICAgICAgIG5hbWU6ICdydW0tanMnLFxuICAgICAgICAgIHZlcnNpb246IGNmZy52ZXJzaW9uXG4gICAgICAgIH0sXG4gICAgICAgIGxhbmd1YWdlOiB7XG4gICAgICAgICAgbmFtZTogJ2phdmFzY3JpcHQnXG4gICAgICAgIH0sXG4gICAgICAgIGVudmlyb25tZW50OiBjZmcuZ2V0KCdlbnZpcm9ubWVudCcpXG4gICAgICB9LFxuICAgICAgbGFiZWxzOiBjZmcuZ2V0KCdjb250ZXh0LnRhZ3MnKVxuICAgIH07XG4gICAgcmV0dXJuIHRydW5jYXRlTW9kZWwoTUVUQURBVEFfTU9ERUwsIG1ldGFkYXRhKTtcbiAgfTtcblxuICBfcHJvdG8uYWRkRXJyb3IgPSBmdW5jdGlvbiBhZGRFcnJvcihlcnJvcikge1xuICAgIHZhciBfdGhpcyR0aHJvdHRsZUV2ZW50cztcblxuICAgIHRoaXMudGhyb3R0bGVFdmVudHMoKF90aGlzJHRocm90dGxlRXZlbnRzID0ge30sIF90aGlzJHRocm90dGxlRXZlbnRzW0VSUk9SU10gPSBlcnJvciwgX3RoaXMkdGhyb3R0bGVFdmVudHMpKTtcbiAgfTtcblxuICBfcHJvdG8uYWRkVHJhbnNhY3Rpb24gPSBmdW5jdGlvbiBhZGRUcmFuc2FjdGlvbih0cmFuc2FjdGlvbikge1xuICAgIHZhciBfdGhpcyR0aHJvdHRsZUV2ZW50czI7XG5cbiAgICB0aGlzLnRocm90dGxlRXZlbnRzKChfdGhpcyR0aHJvdHRsZUV2ZW50czIgPSB7fSwgX3RoaXMkdGhyb3R0bGVFdmVudHMyW1RSQU5TQUNUSU9OU10gPSB0cmFuc2FjdGlvbiwgX3RoaXMkdGhyb3R0bGVFdmVudHMyKSk7XG4gIH07XG5cbiAgX3Byb3RvLm5kanNvbkVycm9ycyA9IGZ1bmN0aW9uIG5kanNvbkVycm9ycyhlcnJvcnMsIGNvbXByZXNzKSB7XG4gICAgdmFyIGtleSA9IGNvbXByZXNzID8gJ2UnIDogJ2Vycm9yJztcbiAgICByZXR1cm4gZXJyb3JzLm1hcChmdW5jdGlvbiAoZXJyb3IpIHtcbiAgICAgIHZhciBfTkRKU09OJHN0cmluZ2lmeTtcblxuICAgICAgcmV0dXJuIE5ESlNPTi5zdHJpbmdpZnkoKF9OREpTT04kc3RyaW5naWZ5ID0ge30sIF9OREpTT04kc3RyaW5naWZ5W2tleV0gPSBjb21wcmVzcyA/IGNvbXByZXNzRXJyb3IoZXJyb3IpIDogZXJyb3IsIF9OREpTT04kc3RyaW5naWZ5KSk7XG4gICAgfSk7XG4gIH07XG5cbiAgX3Byb3RvLm5kanNvbk1ldHJpY3NldHMgPSBmdW5jdGlvbiBuZGpzb25NZXRyaWNzZXRzKG1ldHJpY3NldHMpIHtcbiAgICByZXR1cm4gbWV0cmljc2V0cy5tYXAoZnVuY3Rpb24gKG1ldHJpY3NldCkge1xuICAgICAgcmV0dXJuIE5ESlNPTi5zdHJpbmdpZnkoe1xuICAgICAgICBtZXRyaWNzZXQ6IG1ldHJpY3NldFxuICAgICAgfSk7XG4gICAgfSkuam9pbignJyk7XG4gIH07XG5cbiAgX3Byb3RvLm5kanNvblRyYW5zYWN0aW9ucyA9IGZ1bmN0aW9uIG5kanNvblRyYW5zYWN0aW9ucyh0cmFuc2FjdGlvbnMsIGNvbXByZXNzKSB7XG4gICAgdmFyIF90aGlzNCA9IHRoaXM7XG5cbiAgICB2YXIga2V5ID0gY29tcHJlc3MgPyAneCcgOiAndHJhbnNhY3Rpb24nO1xuICAgIHJldHVybiB0cmFuc2FjdGlvbnMubWFwKGZ1bmN0aW9uICh0cikge1xuICAgICAgdmFyIF9OREpTT04kc3RyaW5naWZ5MjtcblxuICAgICAgdmFyIHNwYW5zID0gJycsXG4gICAgICAgICAgYnJlYWtkb3ducyA9ICcnO1xuXG4gICAgICBpZiAoIWNvbXByZXNzKSB7XG4gICAgICAgIGlmICh0ci5zcGFucykge1xuICAgICAgICAgIHNwYW5zID0gdHIuc3BhbnMubWFwKGZ1bmN0aW9uIChzcGFuKSB7XG4gICAgICAgICAgICByZXR1cm4gTkRKU09OLnN0cmluZ2lmeSh7XG4gICAgICAgICAgICAgIHNwYW46IHNwYW5cbiAgICAgICAgICAgIH0pO1xuICAgICAgICAgIH0pLmpvaW4oJycpO1xuICAgICAgICAgIGRlbGV0ZSB0ci5zcGFucztcbiAgICAgICAgfVxuXG4gICAgICAgIGlmICh0ci5icmVha2Rvd24pIHtcbiAgICAgICAgICBicmVha2Rvd25zID0gX3RoaXM0Lm5kanNvbk1ldHJpY3NldHModHIuYnJlYWtkb3duKTtcbiAgICAgICAgICBkZWxldGUgdHIuYnJlYWtkb3duO1xuICAgICAgICB9XG4gICAgICB9XG5cbiAgICAgIHJldHVybiBOREpTT04uc3RyaW5naWZ5KChfTkRKU09OJHN0cmluZ2lmeTIgPSB7fSwgX05ESlNPTiRzdHJpbmdpZnkyW2tleV0gPSBjb21wcmVzcyA/IGNvbXByZXNzVHJhbnNhY3Rpb24odHIpIDogdHIsIF9OREpTT04kc3RyaW5naWZ5MikpICsgc3BhbnMgKyBicmVha2Rvd25zO1xuICAgIH0pO1xuICB9O1xuXG4gIF9wcm90by5zZW5kRXZlbnRzID0gZnVuY3Rpb24gc2VuZEV2ZW50cyhldmVudHMpIHtcbiAgICB2YXIgX3BheWxvYWQsIF9OREpTT04kc3RyaW5naWZ5MztcblxuICAgIGlmIChldmVudHMubGVuZ3RoID09PSAwKSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgdmFyIHRyYW5zYWN0aW9ucyA9IFtdO1xuICAgIHZhciBlcnJvcnMgPSBbXTtcblxuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgZXZlbnRzLmxlbmd0aDsgaSsrKSB7XG4gICAgICB2YXIgZXZlbnQgPSBldmVudHNbaV07XG5cbiAgICAgIGlmIChldmVudFtUUkFOU0FDVElPTlNdKSB7XG4gICAgICAgIHRyYW5zYWN0aW9ucy5wdXNoKGV2ZW50W1RSQU5TQUNUSU9OU10pO1xuICAgICAgfVxuXG4gICAgICBpZiAoZXZlbnRbRVJST1JTXSkge1xuICAgICAgICBlcnJvcnMucHVzaChldmVudFtFUlJPUlNdKTtcbiAgICAgIH1cbiAgICB9XG5cbiAgICBpZiAodHJhbnNhY3Rpb25zLmxlbmd0aCA9PT0gMCAmJiBlcnJvcnMubGVuZ3RoID09PSAwKSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgdmFyIGNmZyA9IHRoaXMuX2NvbmZpZ1NlcnZpY2U7XG4gICAgdmFyIHBheWxvYWQgPSAoX3BheWxvYWQgPSB7fSwgX3BheWxvYWRbVFJBTlNBQ1RJT05TXSA9IHRyYW5zYWN0aW9ucywgX3BheWxvYWRbRVJST1JTXSA9IGVycm9ycywgX3BheWxvYWQpO1xuICAgIHZhciBmaWx0ZXJlZFBheWxvYWQgPSBjZmcuYXBwbHlGaWx0ZXJzKHBheWxvYWQpO1xuXG4gICAgaWYgKCFmaWx0ZXJlZFBheWxvYWQpIHtcbiAgICAgIHRoaXMuX2xvZ2dpbmdTZXJ2aWNlLndhcm4oJ0Ryb3BwZWQgcGF5bG9hZCBkdWUgdG8gZmlsdGVyaW5nIScpO1xuXG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgdmFyIGFwaVZlcnNpb24gPSBjZmcuZ2V0KCdhcGlWZXJzaW9uJyk7XG4gICAgdmFyIGNvbXByZXNzID0gYXBpVmVyc2lvbiA+IDI7XG4gICAgdmFyIG5kanNvbiA9IFtdO1xuICAgIHZhciBtZXRhZGF0YSA9IHRoaXMuY3JlYXRlTWV0YURhdGEoKTtcbiAgICB2YXIgbWV0YWRhdGFLZXkgPSBjb21wcmVzcyA/ICdtJyA6ICdtZXRhZGF0YSc7XG4gICAgbmRqc29uLnB1c2goTkRKU09OLnN0cmluZ2lmeSgoX05ESlNPTiRzdHJpbmdpZnkzID0ge30sIF9OREpTT04kc3RyaW5naWZ5M1ttZXRhZGF0YUtleV0gPSBjb21wcmVzcyA/IGNvbXByZXNzTWV0YWRhdGEobWV0YWRhdGEpIDogbWV0YWRhdGEsIF9OREpTT04kc3RyaW5naWZ5MykpKTtcbiAgICBuZGpzb24gPSBuZGpzb24uY29uY2F0KHRoaXMubmRqc29uRXJyb3JzKGZpbHRlcmVkUGF5bG9hZFtFUlJPUlNdLCBjb21wcmVzcyksIHRoaXMubmRqc29uVHJhbnNhY3Rpb25zKGZpbHRlcmVkUGF5bG9hZFtUUkFOU0FDVElPTlNdLCBjb21wcmVzcykpO1xuICAgIHZhciBuZGpzb25QYXlsb2FkID0gbmRqc29uLmpvaW4oJycpO1xuXG4gICAgdmFyIF90aGlzJGdldEVuZHBvaW50czIgPSB0aGlzLmdldEVuZHBvaW50cygpLFxuICAgICAgICBpbnRha2VFbmRwb2ludCA9IF90aGlzJGdldEVuZHBvaW50czIuaW50YWtlRW5kcG9pbnQ7XG5cbiAgICByZXR1cm4gdGhpcy5fcG9zdEpzb24oaW50YWtlRW5kcG9pbnQsIG5kanNvblBheWxvYWQpO1xuICB9O1xuXG4gIF9wcm90by5nZXRFbmRwb2ludHMgPSBmdW5jdGlvbiBnZXRFbmRwb2ludHMoKSB7XG4gICAgdmFyIHNlcnZlclVybCA9IHRoaXMuX2NvbmZpZ1NlcnZpY2UuZ2V0KCdzZXJ2ZXJVcmwnKTtcblxuICAgIHZhciBhcGlWZXJzaW9uID0gdGhpcy5fY29uZmlnU2VydmljZS5nZXQoJ2FwaVZlcnNpb24nKTtcblxuICAgIHZhciBzZXJ2ZXJVcmxQcmVmaXggPSB0aGlzLl9jb25maWdTZXJ2aWNlLmdldCgnc2VydmVyVXJsUHJlZml4JykgfHwgXCIvaW50YWtlL3ZcIiArIGFwaVZlcnNpb24gKyBcIi9ydW0vZXZlbnRzXCI7XG4gICAgdmFyIGludGFrZUVuZHBvaW50ID0gc2VydmVyVXJsICsgc2VydmVyVXJsUHJlZml4O1xuICAgIHZhciBjb25maWdFbmRwb2ludCA9IHNlcnZlclVybCArIFwiL2NvbmZpZy92MS9ydW0vYWdlbnRzXCI7XG4gICAgcmV0dXJuIHtcbiAgICAgIGludGFrZUVuZHBvaW50OiBpbnRha2VFbmRwb2ludCxcbiAgICAgIGNvbmZpZ0VuZHBvaW50OiBjb25maWdFbmRwb2ludFxuICAgIH07XG4gIH07XG5cbiAgcmV0dXJuIEFwbVNlcnZlcjtcbn0oKTtcblxuZXhwb3J0IGRlZmF1bHQgQXBtU2VydmVyOyIsImltcG9ydCB7IFByb21pc2UgfSBmcm9tICcuL3BvbHlmaWxscyc7XG5pbXBvcnQgeyBOQVZJR0FUSU9OX1RJTUlOR19NQVJLUywgQ09NUFJFU1NFRF9OQVZfVElNSU5HX01BUktTIH0gZnJvbSAnLi4vcGVyZm9ybWFuY2UtbW9uaXRvcmluZy9jYXB0dXJlLW5hdmlnYXRpb24nO1xuaW1wb3J0IHsgaXNCZWFjb25JbnNwZWN0aW9uRW5hYmxlZCB9IGZyb20gJy4vdXRpbHMnO1xuXG5mdW5jdGlvbiBjb21wcmVzc1N0YWNrRnJhbWVzKGZyYW1lcykge1xuICByZXR1cm4gZnJhbWVzLm1hcChmdW5jdGlvbiAoZnJhbWUpIHtcbiAgICByZXR1cm4ge1xuICAgICAgYXA6IGZyYW1lLmFic19wYXRoLFxuICAgICAgZjogZnJhbWUuZmlsZW5hbWUsXG4gICAgICBmbjogZnJhbWUuZnVuY3Rpb24sXG4gICAgICBsaTogZnJhbWUubGluZW5vLFxuICAgICAgY286IGZyYW1lLmNvbG5vXG4gICAgfTtcbiAgfSk7XG59XG5cbmZ1bmN0aW9uIGNvbXByZXNzUmVzcG9uc2UocmVzcG9uc2UpIHtcbiAgcmV0dXJuIHtcbiAgICB0czogcmVzcG9uc2UudHJhbnNmZXJfc2l6ZSxcbiAgICBlYnM6IHJlc3BvbnNlLmVuY29kZWRfYm9keV9zaXplLFxuICAgIGRiczogcmVzcG9uc2UuZGVjb2RlZF9ib2R5X3NpemVcbiAgfTtcbn1cblxuZnVuY3Rpb24gY29tcHJlc3NIVFRQKGh0dHApIHtcbiAgdmFyIGNvbXByZXNzZWQgPSB7fTtcbiAgdmFyIG1ldGhvZCA9IGh0dHAubWV0aG9kLFxuICAgICAgc3RhdHVzX2NvZGUgPSBodHRwLnN0YXR1c19jb2RlLFxuICAgICAgdXJsID0gaHR0cC51cmwsXG4gICAgICByZXNwb25zZSA9IGh0dHAucmVzcG9uc2U7XG4gIGNvbXByZXNzZWQudXJsID0gdXJsO1xuXG4gIGlmIChtZXRob2QpIHtcbiAgICBjb21wcmVzc2VkLm10ID0gbWV0aG9kO1xuICB9XG5cbiAgaWYgKHN0YXR1c19jb2RlKSB7XG4gICAgY29tcHJlc3NlZC5zYyA9IHN0YXR1c19jb2RlO1xuICB9XG5cbiAgaWYgKHJlc3BvbnNlKSB7XG4gICAgY29tcHJlc3NlZC5yID0gY29tcHJlc3NSZXNwb25zZShyZXNwb25zZSk7XG4gIH1cblxuICByZXR1cm4gY29tcHJlc3NlZDtcbn1cblxuZnVuY3Rpb24gY29tcHJlc3NDb250ZXh0KGNvbnRleHQpIHtcbiAgaWYgKCFjb250ZXh0KSB7XG4gICAgcmV0dXJuIG51bGw7XG4gIH1cblxuICB2YXIgY29tcHJlc3NlZCA9IHt9O1xuICB2YXIgcGFnZSA9IGNvbnRleHQucGFnZSxcbiAgICAgIGh0dHAgPSBjb250ZXh0Lmh0dHAsXG4gICAgICByZXNwb25zZSA9IGNvbnRleHQucmVzcG9uc2UsXG4gICAgICBkZXN0aW5hdGlvbiA9IGNvbnRleHQuZGVzdGluYXRpb24sXG4gICAgICB1c2VyID0gY29udGV4dC51c2VyLFxuICAgICAgY3VzdG9tID0gY29udGV4dC5jdXN0b207XG5cbiAgaWYgKHBhZ2UpIHtcbiAgICBjb21wcmVzc2VkLnAgPSB7XG4gICAgICByZjogcGFnZS5yZWZlcmVyLFxuICAgICAgdXJsOiBwYWdlLnVybFxuICAgIH07XG4gIH1cblxuICBpZiAoaHR0cCkge1xuICAgIGNvbXByZXNzZWQuaCA9IGNvbXByZXNzSFRUUChodHRwKTtcbiAgfVxuXG4gIGlmIChyZXNwb25zZSkge1xuICAgIGNvbXByZXNzZWQuciA9IGNvbXByZXNzUmVzcG9uc2UocmVzcG9uc2UpO1xuICB9XG5cbiAgaWYgKGRlc3RpbmF0aW9uKSB7XG4gICAgdmFyIHNlcnZpY2UgPSBkZXN0aW5hdGlvbi5zZXJ2aWNlO1xuICAgIGNvbXByZXNzZWQuZHQgPSB7XG4gICAgICBzZToge1xuICAgICAgICBuOiBzZXJ2aWNlLm5hbWUsXG4gICAgICAgIHQ6IHNlcnZpY2UudHlwZSxcbiAgICAgICAgcmM6IHNlcnZpY2UucmVzb3VyY2VcbiAgICAgIH0sXG4gICAgICBhZDogZGVzdGluYXRpb24uYWRkcmVzcyxcbiAgICAgIHBvOiBkZXN0aW5hdGlvbi5wb3J0XG4gICAgfTtcbiAgfVxuXG4gIGlmICh1c2VyKSB7XG4gICAgY29tcHJlc3NlZC51ID0ge1xuICAgICAgaWQ6IHVzZXIuaWQsXG4gICAgICB1bjogdXNlci51c2VybmFtZSxcbiAgICAgIGVtOiB1c2VyLmVtYWlsXG4gICAgfTtcbiAgfVxuXG4gIGlmIChjdXN0b20pIHtcbiAgICBjb21wcmVzc2VkLmN1ID0gY3VzdG9tO1xuICB9XG5cbiAgcmV0dXJuIGNvbXByZXNzZWQ7XG59XG5cbmZ1bmN0aW9uIGNvbXByZXNzTWFya3MobWFya3MpIHtcbiAgaWYgKCFtYXJrcykge1xuICAgIHJldHVybiBudWxsO1xuICB9XG5cbiAgdmFyIGNvbXByZXNzZWROdE1hcmtzID0gY29tcHJlc3NOYXZpZ2F0aW9uVGltaW5nTWFya3MobWFya3MubmF2aWdhdGlvblRpbWluZyk7XG4gIHZhciBjb21wcmVzc2VkID0ge1xuICAgIG50OiBjb21wcmVzc2VkTnRNYXJrcyxcbiAgICBhOiBjb21wcmVzc0FnZW50TWFya3MoY29tcHJlc3NlZE50TWFya3MsIG1hcmtzLmFnZW50KVxuICB9O1xuICByZXR1cm4gY29tcHJlc3NlZDtcbn1cblxuZnVuY3Rpb24gY29tcHJlc3NOYXZpZ2F0aW9uVGltaW5nTWFya3MobnRNYXJrcykge1xuICBpZiAoIW50TWFya3MpIHtcbiAgICByZXR1cm4gbnVsbDtcbiAgfVxuXG4gIHZhciBjb21wcmVzc2VkID0ge307XG4gIENPTVBSRVNTRURfTkFWX1RJTUlOR19NQVJLUy5mb3JFYWNoKGZ1bmN0aW9uIChtYXJrLCBpbmRleCkge1xuICAgIHZhciBtYXBwaW5nID0gTkFWSUdBVElPTl9USU1JTkdfTUFSS1NbaW5kZXhdO1xuICAgIGNvbXByZXNzZWRbbWFya10gPSBudE1hcmtzW21hcHBpbmddO1xuICB9KTtcbiAgcmV0dXJuIGNvbXByZXNzZWQ7XG59XG5cbmZ1bmN0aW9uIGNvbXByZXNzQWdlbnRNYXJrcyhjb21wcmVzc2VkTnRNYXJrcywgYWdlbnRNYXJrcykge1xuICB2YXIgY29tcHJlc3NlZCA9IHt9O1xuXG4gIGlmIChjb21wcmVzc2VkTnRNYXJrcykge1xuICAgIGNvbXByZXNzZWQgPSB7XG4gICAgICBmYjogY29tcHJlc3NlZE50TWFya3MucnMsXG4gICAgICBkaTogY29tcHJlc3NlZE50TWFya3MuZGksXG4gICAgICBkYzogY29tcHJlc3NlZE50TWFya3MuZGNcbiAgICB9O1xuICB9XG5cbiAgaWYgKGFnZW50TWFya3MpIHtcbiAgICB2YXIgZnAgPSBhZ2VudE1hcmtzLmZpcnN0Q29udGVudGZ1bFBhaW50O1xuICAgIHZhciBscCA9IGFnZW50TWFya3MubGFyZ2VzdENvbnRlbnRmdWxQYWludDtcblxuICAgIGlmIChmcCkge1xuICAgICAgY29tcHJlc3NlZC5mcCA9IGZwO1xuICAgIH1cblxuICAgIGlmIChscCkge1xuICAgICAgY29tcHJlc3NlZC5scCA9IGxwO1xuICAgIH1cbiAgfVxuXG4gIGlmIChPYmplY3Qua2V5cyhjb21wcmVzc2VkKS5sZW5ndGggPT09IDApIHtcbiAgICByZXR1cm4gbnVsbDtcbiAgfVxuXG4gIHJldHVybiBjb21wcmVzc2VkO1xufVxuXG5leHBvcnQgZnVuY3Rpb24gY29tcHJlc3NNZXRhZGF0YShtZXRhZGF0YSkge1xuICB2YXIgc2VydmljZSA9IG1ldGFkYXRhLnNlcnZpY2UsXG4gICAgICBsYWJlbHMgPSBtZXRhZGF0YS5sYWJlbHM7XG4gIHZhciBhZ2VudCA9IHNlcnZpY2UuYWdlbnQsXG4gICAgICBsYW5ndWFnZSA9IHNlcnZpY2UubGFuZ3VhZ2U7XG4gIHJldHVybiB7XG4gICAgc2U6IHtcbiAgICAgIG46IHNlcnZpY2UubmFtZSxcbiAgICAgIHZlOiBzZXJ2aWNlLnZlcnNpb24sXG4gICAgICBhOiB7XG4gICAgICAgIG46IGFnZW50Lm5hbWUsXG4gICAgICAgIHZlOiBhZ2VudC52ZXJzaW9uXG4gICAgICB9LFxuICAgICAgbGE6IHtcbiAgICAgICAgbjogbGFuZ3VhZ2UubmFtZVxuICAgICAgfSxcbiAgICAgIGVuOiBzZXJ2aWNlLmVudmlyb25tZW50XG4gICAgfSxcbiAgICBsOiBsYWJlbHNcbiAgfTtcbn1cbmV4cG9ydCBmdW5jdGlvbiBjb21wcmVzc1RyYW5zYWN0aW9uKHRyYW5zYWN0aW9uKSB7XG4gIHZhciBzcGFucyA9IHRyYW5zYWN0aW9uLnNwYW5zLm1hcChmdW5jdGlvbiAoc3Bhbikge1xuICAgIHZhciBzcGFuRGF0YSA9IHtcbiAgICAgIGlkOiBzcGFuLmlkLFxuICAgICAgbjogc3Bhbi5uYW1lLFxuICAgICAgdDogc3Bhbi50eXBlLFxuICAgICAgczogc3Bhbi5zdGFydCxcbiAgICAgIGQ6IHNwYW4uZHVyYXRpb24sXG4gICAgICBjOiBjb21wcmVzc0NvbnRleHQoc3Bhbi5jb250ZXh0KSxcbiAgICAgIG86IHNwYW4ub3V0Y29tZSxcbiAgICAgIHNyOiBzcGFuLnNhbXBsZV9yYXRlXG4gICAgfTtcblxuICAgIGlmIChzcGFuLnBhcmVudF9pZCAhPT0gdHJhbnNhY3Rpb24uaWQpIHtcbiAgICAgIHNwYW5EYXRhLnBpZCA9IHNwYW4ucGFyZW50X2lkO1xuICAgIH1cblxuICAgIGlmIChzcGFuLnN5bmMgPT09IHRydWUpIHtcbiAgICAgIHNwYW5EYXRhLnN5ID0gdHJ1ZTtcbiAgICB9XG5cbiAgICBpZiAoc3Bhbi5zdWJ0eXBlKSB7XG4gICAgICBzcGFuRGF0YS5zdSA9IHNwYW4uc3VidHlwZTtcbiAgICB9XG5cbiAgICBpZiAoc3Bhbi5hY3Rpb24pIHtcbiAgICAgIHNwYW5EYXRhLmFjID0gc3Bhbi5hY3Rpb247XG4gICAgfVxuXG4gICAgcmV0dXJuIHNwYW5EYXRhO1xuICB9KTtcbiAgdmFyIHRyID0ge1xuICAgIGlkOiB0cmFuc2FjdGlvbi5pZCxcbiAgICB0aWQ6IHRyYW5zYWN0aW9uLnRyYWNlX2lkLFxuICAgIG46IHRyYW5zYWN0aW9uLm5hbWUsXG4gICAgdDogdHJhbnNhY3Rpb24udHlwZSxcbiAgICBkOiB0cmFuc2FjdGlvbi5kdXJhdGlvbixcbiAgICBjOiBjb21wcmVzc0NvbnRleHQodHJhbnNhY3Rpb24uY29udGV4dCksXG4gICAgazogY29tcHJlc3NNYXJrcyh0cmFuc2FjdGlvbi5tYXJrcyksXG4gICAgbWU6IGNvbXByZXNzTWV0cmljc2V0cyh0cmFuc2FjdGlvbi5icmVha2Rvd24pLFxuICAgIHk6IHNwYW5zLFxuICAgIHljOiB7XG4gICAgICBzZDogc3BhbnMubGVuZ3RoXG4gICAgfSxcbiAgICBzbTogdHJhbnNhY3Rpb24uc2FtcGxlZCxcbiAgICBzcjogdHJhbnNhY3Rpb24uc2FtcGxlX3JhdGUsXG4gICAgbzogdHJhbnNhY3Rpb24ub3V0Y29tZVxuICB9O1xuXG4gIGlmICh0cmFuc2FjdGlvbi5leHBlcmllbmNlKSB7XG4gICAgdmFyIF90cmFuc2FjdGlvbiRleHBlcmllbiA9IHRyYW5zYWN0aW9uLmV4cGVyaWVuY2UsXG4gICAgICAgIGNscyA9IF90cmFuc2FjdGlvbiRleHBlcmllbi5jbHMsXG4gICAgICAgIGZpZCA9IF90cmFuc2FjdGlvbiRleHBlcmllbi5maWQsXG4gICAgICAgIHRidCA9IF90cmFuc2FjdGlvbiRleHBlcmllbi50YnQsXG4gICAgICAgIGxvbmd0YXNrID0gX3RyYW5zYWN0aW9uJGV4cGVyaWVuLmxvbmd0YXNrO1xuICAgIHRyLmV4cCA9IHtcbiAgICAgIGNsczogY2xzLFxuICAgICAgZmlkOiBmaWQsXG4gICAgICB0YnQ6IHRidCxcbiAgICAgIGx0OiBsb25ndGFza1xuICAgIH07XG4gIH1cblxuICBpZiAodHJhbnNhY3Rpb24uc2Vzc2lvbikge1xuICAgIHZhciBfdHJhbnNhY3Rpb24kc2Vzc2lvbiA9IHRyYW5zYWN0aW9uLnNlc3Npb24sXG4gICAgICAgIGlkID0gX3RyYW5zYWN0aW9uJHNlc3Npb24uaWQsXG4gICAgICAgIHNlcXVlbmNlID0gX3RyYW5zYWN0aW9uJHNlc3Npb24uc2VxdWVuY2U7XG4gICAgdHIuc2VzID0ge1xuICAgICAgaWQ6IGlkLFxuICAgICAgc2VxOiBzZXF1ZW5jZVxuICAgIH07XG4gIH1cblxuICByZXR1cm4gdHI7XG59XG5leHBvcnQgZnVuY3Rpb24gY29tcHJlc3NFcnJvcihlcnJvcikge1xuICB2YXIgZXhjZXB0aW9uID0gZXJyb3IuZXhjZXB0aW9uO1xuICB2YXIgY29tcHJlc3NlZCA9IHtcbiAgICBpZDogZXJyb3IuaWQsXG4gICAgY2w6IGVycm9yLmN1bHByaXQsXG4gICAgZXg6IHtcbiAgICAgIG1nOiBleGNlcHRpb24ubWVzc2FnZSxcbiAgICAgIHN0OiBjb21wcmVzc1N0YWNrRnJhbWVzKGV4Y2VwdGlvbi5zdGFja3RyYWNlKSxcbiAgICAgIHQ6IGVycm9yLnR5cGVcbiAgICB9LFxuICAgIGM6IGNvbXByZXNzQ29udGV4dChlcnJvci5jb250ZXh0KVxuICB9O1xuICB2YXIgdHJhbnNhY3Rpb24gPSBlcnJvci50cmFuc2FjdGlvbjtcblxuICBpZiAodHJhbnNhY3Rpb24pIHtcbiAgICBjb21wcmVzc2VkLnRpZCA9IGVycm9yLnRyYWNlX2lkO1xuICAgIGNvbXByZXNzZWQucGlkID0gZXJyb3IucGFyZW50X2lkO1xuICAgIGNvbXByZXNzZWQueGlkID0gZXJyb3IudHJhbnNhY3Rpb25faWQ7XG4gICAgY29tcHJlc3NlZC54ID0ge1xuICAgICAgdDogdHJhbnNhY3Rpb24udHlwZSxcbiAgICAgIHNtOiB0cmFuc2FjdGlvbi5zYW1wbGVkXG4gICAgfTtcbiAgfVxuXG4gIHJldHVybiBjb21wcmVzc2VkO1xufVxuZXhwb3J0IGZ1bmN0aW9uIGNvbXByZXNzTWV0cmljc2V0cyhicmVha2Rvd25zKSB7XG4gIHJldHVybiBicmVha2Rvd25zLm1hcChmdW5jdGlvbiAoX3JlZikge1xuICAgIHZhciBzcGFuID0gX3JlZi5zcGFuLFxuICAgICAgICBzYW1wbGVzID0gX3JlZi5zYW1wbGVzO1xuICAgIHZhciBpc1NwYW4gPSBzcGFuICE9IG51bGw7XG5cbiAgICBpZiAoaXNTcGFuKSB7XG4gICAgICByZXR1cm4ge1xuICAgICAgICB5OiB7XG4gICAgICAgICAgdDogc3Bhbi50eXBlXG4gICAgICAgIH0sXG4gICAgICAgIHNhOiB7XG4gICAgICAgICAgeXNjOiB7XG4gICAgICAgICAgICB2OiBzYW1wbGVzWydzcGFuLnNlbGZfdGltZS5jb3VudCddLnZhbHVlXG4gICAgICAgICAgfSxcbiAgICAgICAgICB5c3M6IHtcbiAgICAgICAgICAgIHY6IHNhbXBsZXNbJ3NwYW4uc2VsZl90aW1lLnN1bS51cyddLnZhbHVlXG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICB9O1xuICAgIH1cblxuICAgIHJldHVybiB7XG4gICAgICBzYToge1xuICAgICAgICB4ZGM6IHtcbiAgICAgICAgICB2OiBzYW1wbGVzWyd0cmFuc2FjdGlvbi5kdXJhdGlvbi5jb3VudCddLnZhbHVlXG4gICAgICAgIH0sXG4gICAgICAgIHhkczoge1xuICAgICAgICAgIHY6IHNhbXBsZXNbJ3RyYW5zYWN0aW9uLmR1cmF0aW9uLnN1bS51cyddLnZhbHVlXG4gICAgICAgIH0sXG4gICAgICAgIHhiYzoge1xuICAgICAgICAgIHY6IHNhbXBsZXNbJ3RyYW5zYWN0aW9uLmJyZWFrZG93bi5jb3VudCddLnZhbHVlXG4gICAgICAgIH1cbiAgICAgIH1cbiAgICB9O1xuICB9KTtcbn1cbmV4cG9ydCBmdW5jdGlvbiBjb21wcmVzc1BheWxvYWQocGFyYW1zLCB0eXBlKSB7XG4gIGlmICh0eXBlID09PSB2b2lkIDApIHtcbiAgICB0eXBlID0gJ2d6aXAnO1xuICB9XG5cbiAgdmFyIGlzQ29tcHJlc3Npb25TdHJlYW1TdXBwb3J0ZWQgPSB0eXBlb2YgQ29tcHJlc3Npb25TdHJlYW0gPT09ICdmdW5jdGlvbic7XG4gIHJldHVybiBuZXcgUHJvbWlzZShmdW5jdGlvbiAocmVzb2x2ZSkge1xuICAgIGlmICghaXNDb21wcmVzc2lvblN0cmVhbVN1cHBvcnRlZCkge1xuICAgICAgcmV0dXJuIHJlc29sdmUocGFyYW1zKTtcbiAgICB9XG5cbiAgICBpZiAoaXNCZWFjb25JbnNwZWN0aW9uRW5hYmxlZCgpKSB7XG4gICAgICByZXR1cm4gcmVzb2x2ZShwYXJhbXMpO1xuICAgIH1cblxuICAgIHZhciBwYXlsb2FkID0gcGFyYW1zLnBheWxvYWQsXG4gICAgICAgIGhlYWRlcnMgPSBwYXJhbXMuaGVhZGVycyxcbiAgICAgICAgYmVmb3JlU2VuZCA9IHBhcmFtcy5iZWZvcmVTZW5kO1xuICAgIHZhciBwYXlsb2FkU3RyZWFtID0gbmV3IEJsb2IoW3BheWxvYWRdKS5zdHJlYW0oKTtcbiAgICB2YXIgY29tcHJlc3NlZFN0cmVhbSA9IHBheWxvYWRTdHJlYW0ucGlwZVRocm91Z2gobmV3IENvbXByZXNzaW9uU3RyZWFtKHR5cGUpKTtcbiAgICByZXR1cm4gbmV3IFJlc3BvbnNlKGNvbXByZXNzZWRTdHJlYW0pLmJsb2IoKS50aGVuKGZ1bmN0aW9uIChwYXlsb2FkKSB7XG4gICAgICBoZWFkZXJzWydDb250ZW50LUVuY29kaW5nJ10gPSB0eXBlO1xuICAgICAgcmV0dXJuIHJlc29sdmUoe1xuICAgICAgICBwYXlsb2FkOiBwYXlsb2FkLFxuICAgICAgICBoZWFkZXJzOiBoZWFkZXJzLFxuICAgICAgICBiZWZvcmVTZW5kOiBiZWZvcmVTZW5kXG4gICAgICB9KTtcbiAgICB9KTtcbiAgfSk7XG59IiwiZnVuY3Rpb24gX2V4dGVuZHMoKSB7IF9leHRlbmRzID0gT2JqZWN0LmFzc2lnbiB8fCBmdW5jdGlvbiAodGFyZ2V0KSB7IGZvciAodmFyIGkgPSAxOyBpIDwgYXJndW1lbnRzLmxlbmd0aDsgaSsrKSB7IHZhciBzb3VyY2UgPSBhcmd1bWVudHNbaV07IGZvciAodmFyIGtleSBpbiBzb3VyY2UpIHsgaWYgKE9iamVjdC5wcm90b3R5cGUuaGFzT3duUHJvcGVydHkuY2FsbChzb3VyY2UsIGtleSkpIHsgdGFyZ2V0W2tleV0gPSBzb3VyY2Vba2V5XTsgfSB9IH0gcmV0dXJuIHRhcmdldDsgfTsgcmV0dXJuIF9leHRlbmRzLmFwcGx5KHRoaXMsIGFyZ3VtZW50cyk7IH1cblxuaW1wb3J0IHsgZ2V0Q3VycmVudFNjcmlwdCwgc2V0TGFiZWwsIG1lcmdlLCBleHRlbmQsIGlzVW5kZWZpbmVkIH0gZnJvbSAnLi91dGlscyc7XG5pbXBvcnQgRXZlbnRIYW5kbGVyIGZyb20gJy4vZXZlbnQtaGFuZGxlcic7XG5pbXBvcnQgeyBDT05GSUdfQ0hBTkdFLCBMT0NBTF9DT05GSUdfS0VZIH0gZnJvbSAnLi9jb25zdGFudHMnO1xuXG5mdW5jdGlvbiBnZXRDb25maWdGcm9tU2NyaXB0KCkge1xuICB2YXIgc2NyaXB0ID0gZ2V0Q3VycmVudFNjcmlwdCgpO1xuICB2YXIgY29uZmlnID0gZ2V0RGF0YUF0dHJpYnV0ZXNGcm9tTm9kZShzY3JpcHQpO1xuICByZXR1cm4gY29uZmlnO1xufVxuXG5mdW5jdGlvbiBnZXREYXRhQXR0cmlidXRlc0Zyb21Ob2RlKG5vZGUpIHtcbiAgaWYgKCFub2RlKSB7XG4gICAgcmV0dXJuIHt9O1xuICB9XG5cbiAgdmFyIGRhdGFBdHRycyA9IHt9O1xuICB2YXIgZGF0YVJlZ2V4ID0gL15kYXRhLShbXFx3LV0rKSQvO1xuICB2YXIgYXR0cnMgPSBub2RlLmF0dHJpYnV0ZXM7XG5cbiAgZm9yICh2YXIgaSA9IDA7IGkgPCBhdHRycy5sZW5ndGg7IGkrKykge1xuICAgIHZhciBhdHRyID0gYXR0cnNbaV07XG5cbiAgICBpZiAoZGF0YVJlZ2V4LnRlc3QoYXR0ci5ub2RlTmFtZSkpIHtcbiAgICAgIHZhciBrZXkgPSBhdHRyLm5vZGVOYW1lLm1hdGNoKGRhdGFSZWdleClbMV07XG4gICAgICB2YXIgY2FtZWxDYXNlZGtleSA9IGtleS5zcGxpdCgnLScpLm1hcChmdW5jdGlvbiAodmFsdWUsIGluZGV4KSB7XG4gICAgICAgIHJldHVybiBpbmRleCA+IDAgPyB2YWx1ZS5jaGFyQXQoMCkudG9VcHBlckNhc2UoKSArIHZhbHVlLnN1YnN0cmluZygxKSA6IHZhbHVlO1xuICAgICAgfSkuam9pbignJyk7XG4gICAgICBkYXRhQXR0cnNbY2FtZWxDYXNlZGtleV0gPSBhdHRyLnZhbHVlIHx8IGF0dHIubm9kZVZhbHVlO1xuICAgIH1cbiAgfVxuXG4gIHJldHVybiBkYXRhQXR0cnM7XG59XG5cbnZhciBDb25maWcgPSBmdW5jdGlvbiAoKSB7XG4gIGZ1bmN0aW9uIENvbmZpZygpIHtcbiAgICB0aGlzLmNvbmZpZyA9IHtcbiAgICAgIHNlcnZpY2VOYW1lOiAnJyxcbiAgICAgIHNlcnZpY2VWZXJzaW9uOiAnJyxcbiAgICAgIGVudmlyb25tZW50OiAnJyxcbiAgICAgIHNlcnZlclVybDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODIwMCcsXG4gICAgICBzZXJ2ZXJVcmxQcmVmaXg6ICcnLFxuICAgICAgYWN0aXZlOiB0cnVlLFxuICAgICAgaW5zdHJ1bWVudDogdHJ1ZSxcbiAgICAgIGRpc2FibGVJbnN0cnVtZW50YXRpb25zOiBbXSxcbiAgICAgIGxvZ0xldmVsOiAnd2FybicsXG4gICAgICBicmVha2Rvd25NZXRyaWNzOiBmYWxzZSxcbiAgICAgIGlnbm9yZVRyYW5zYWN0aW9uczogW10sXG4gICAgICBldmVudHNMaW1pdDogODAsXG4gICAgICBxdWV1ZUxpbWl0OiAtMSxcbiAgICAgIGZsdXNoSW50ZXJ2YWw6IDUwMCxcbiAgICAgIGRpc3RyaWJ1dGVkVHJhY2luZzogdHJ1ZSxcbiAgICAgIGRpc3RyaWJ1dGVkVHJhY2luZ09yaWdpbnM6IFtdLFxuICAgICAgZGlzdHJpYnV0ZWRUcmFjaW5nSGVhZGVyTmFtZTogJ3RyYWNlcGFyZW50JyxcbiAgICAgIHBhZ2VMb2FkVHJhY2VJZDogJycsXG4gICAgICBwYWdlTG9hZFNwYW5JZDogJycsXG4gICAgICBwYWdlTG9hZFNhbXBsZWQ6IGZhbHNlLFxuICAgICAgcGFnZUxvYWRUcmFuc2FjdGlvbk5hbWU6ICcnLFxuICAgICAgcHJvcGFnYXRlVHJhY2VzdGF0ZTogZmFsc2UsXG4gICAgICB0cmFuc2FjdGlvblNhbXBsZVJhdGU6IDEuMCxcbiAgICAgIGNlbnRyYWxDb25maWc6IGZhbHNlLFxuICAgICAgbW9uaXRvckxvbmd0YXNrczogdHJ1ZSxcbiAgICAgIGFwaVZlcnNpb246IDIsXG4gICAgICBjb250ZXh0OiB7fSxcbiAgICAgIHNlc3Npb246IGZhbHNlLFxuICAgICAgYXBtUmVxdWVzdDogbnVsbCxcbiAgICAgIHNlbmRDcmVkZW50aWFsczogZmFsc2VcbiAgICB9O1xuICAgIHRoaXMuZXZlbnRzID0gbmV3IEV2ZW50SGFuZGxlcigpO1xuICAgIHRoaXMuZmlsdGVycyA9IFtdO1xuICAgIHRoaXMudmVyc2lvbiA9ICcnO1xuICB9XG5cbiAgdmFyIF9wcm90byA9IENvbmZpZy5wcm90b3R5cGU7XG5cbiAgX3Byb3RvLmluaXQgPSBmdW5jdGlvbiBpbml0KCkge1xuICAgIHZhciBzY3JpcHREYXRhID0gZ2V0Q29uZmlnRnJvbVNjcmlwdCgpO1xuICAgIHRoaXMuc2V0Q29uZmlnKHNjcmlwdERhdGEpO1xuICB9O1xuXG4gIF9wcm90by5zZXRWZXJzaW9uID0gZnVuY3Rpb24gc2V0VmVyc2lvbih2ZXJzaW9uKSB7XG4gICAgdGhpcy52ZXJzaW9uID0gdmVyc2lvbjtcbiAgfTtcblxuICBfcHJvdG8uYWRkRmlsdGVyID0gZnVuY3Rpb24gYWRkRmlsdGVyKGNiKSB7XG4gICAgaWYgKHR5cGVvZiBjYiAhPT0gJ2Z1bmN0aW9uJykge1xuICAgICAgdGhyb3cgbmV3IEVycm9yKCdBcmd1bWVudCB0byBtdXN0IGJlIGZ1bmN0aW9uJyk7XG4gICAgfVxuXG4gICAgdGhpcy5maWx0ZXJzLnB1c2goY2IpO1xuICB9O1xuXG4gIF9wcm90by5hcHBseUZpbHRlcnMgPSBmdW5jdGlvbiBhcHBseUZpbHRlcnMoZGF0YSkge1xuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgdGhpcy5maWx0ZXJzLmxlbmd0aDsgaSsrKSB7XG4gICAgICBkYXRhID0gdGhpcy5maWx0ZXJzW2ldKGRhdGEpO1xuXG4gICAgICBpZiAoIWRhdGEpIHtcbiAgICAgICAgcmV0dXJuO1xuICAgICAgfVxuICAgIH1cblxuICAgIHJldHVybiBkYXRhO1xuICB9O1xuXG4gIF9wcm90by5nZXQgPSBmdW5jdGlvbiBnZXQoa2V5KSB7XG4gICAgcmV0dXJuIGtleS5zcGxpdCgnLicpLnJlZHVjZShmdW5jdGlvbiAob2JqLCBvYmpLZXkpIHtcbiAgICAgIHJldHVybiBvYmogJiYgb2JqW29iaktleV07XG4gICAgfSwgdGhpcy5jb25maWcpO1xuICB9O1xuXG4gIF9wcm90by5zZXRVc2VyQ29udGV4dCA9IGZ1bmN0aW9uIHNldFVzZXJDb250ZXh0KHVzZXJDb250ZXh0KSB7XG4gICAgaWYgKHVzZXJDb250ZXh0ID09PSB2b2lkIDApIHtcbiAgICAgIHVzZXJDb250ZXh0ID0ge307XG4gICAgfVxuXG4gICAgdmFyIGNvbnRleHQgPSB7fTtcbiAgICB2YXIgX3VzZXJDb250ZXh0ID0gdXNlckNvbnRleHQsXG4gICAgICAgIGlkID0gX3VzZXJDb250ZXh0LmlkLFxuICAgICAgICB1c2VybmFtZSA9IF91c2VyQ29udGV4dC51c2VybmFtZSxcbiAgICAgICAgZW1haWwgPSBfdXNlckNvbnRleHQuZW1haWw7XG5cbiAgICBpZiAodHlwZW9mIGlkID09PSAnbnVtYmVyJyB8fCB0eXBlb2YgaWQgPT09ICdzdHJpbmcnKSB7XG4gICAgICBjb250ZXh0LmlkID0gaWQ7XG4gICAgfVxuXG4gICAgaWYgKHR5cGVvZiB1c2VybmFtZSA9PT0gJ3N0cmluZycpIHtcbiAgICAgIGNvbnRleHQudXNlcm5hbWUgPSB1c2VybmFtZTtcbiAgICB9XG5cbiAgICBpZiAodHlwZW9mIGVtYWlsID09PSAnc3RyaW5nJykge1xuICAgICAgY29udGV4dC5lbWFpbCA9IGVtYWlsO1xuICAgIH1cblxuICAgIHRoaXMuY29uZmlnLmNvbnRleHQudXNlciA9IGV4dGVuZCh0aGlzLmNvbmZpZy5jb250ZXh0LnVzZXIgfHwge30sIGNvbnRleHQpO1xuICB9O1xuXG4gIF9wcm90by5zZXRDdXN0b21Db250ZXh0ID0gZnVuY3Rpb24gc2V0Q3VzdG9tQ29udGV4dChjdXN0b21Db250ZXh0KSB7XG4gICAgaWYgKGN1c3RvbUNvbnRleHQgPT09IHZvaWQgMCkge1xuICAgICAgY3VzdG9tQ29udGV4dCA9IHt9O1xuICAgIH1cblxuICAgIHRoaXMuY29uZmlnLmNvbnRleHQuY3VzdG9tID0gZXh0ZW5kKHRoaXMuY29uZmlnLmNvbnRleHQuY3VzdG9tIHx8IHt9LCBjdXN0b21Db250ZXh0KTtcbiAgfTtcblxuICBfcHJvdG8uYWRkTGFiZWxzID0gZnVuY3Rpb24gYWRkTGFiZWxzKHRhZ3MpIHtcbiAgICB2YXIgX3RoaXMgPSB0aGlzO1xuXG4gICAgaWYgKCF0aGlzLmNvbmZpZy5jb250ZXh0LnRhZ3MpIHtcbiAgICAgIHRoaXMuY29uZmlnLmNvbnRleHQudGFncyA9IHt9O1xuICAgIH1cblxuICAgIHZhciBrZXlzID0gT2JqZWN0LmtleXModGFncyk7XG4gICAga2V5cy5mb3JFYWNoKGZ1bmN0aW9uIChrKSB7XG4gICAgICByZXR1cm4gc2V0TGFiZWwoaywgdGFnc1trXSwgX3RoaXMuY29uZmlnLmNvbnRleHQudGFncyk7XG4gICAgfSk7XG4gIH07XG5cbiAgX3Byb3RvLnNldENvbmZpZyA9IGZ1bmN0aW9uIHNldENvbmZpZyhwcm9wZXJ0aWVzKSB7XG4gICAgaWYgKHByb3BlcnRpZXMgPT09IHZvaWQgMCkge1xuICAgICAgcHJvcGVydGllcyA9IHt9O1xuICAgIH1cblxuICAgIHZhciBfcHJvcGVydGllcyA9IHByb3BlcnRpZXMsXG4gICAgICAgIHRyYW5zYWN0aW9uU2FtcGxlUmF0ZSA9IF9wcm9wZXJ0aWVzLnRyYW5zYWN0aW9uU2FtcGxlUmF0ZSxcbiAgICAgICAgc2VydmVyVXJsID0gX3Byb3BlcnRpZXMuc2VydmVyVXJsO1xuXG4gICAgaWYgKHNlcnZlclVybCkge1xuICAgICAgcHJvcGVydGllcy5zZXJ2ZXJVcmwgPSBzZXJ2ZXJVcmwucmVwbGFjZSgvXFwvKyQvLCAnJyk7XG4gICAgfVxuXG4gICAgaWYgKCFpc1VuZGVmaW5lZCh0cmFuc2FjdGlvblNhbXBsZVJhdGUpKSB7XG4gICAgICBpZiAodHJhbnNhY3Rpb25TYW1wbGVSYXRlIDwgMC4wMDAxICYmIHRyYW5zYWN0aW9uU2FtcGxlUmF0ZSA+IDApIHtcbiAgICAgICAgdHJhbnNhY3Rpb25TYW1wbGVSYXRlID0gMC4wMDAxO1xuICAgICAgfVxuXG4gICAgICBwcm9wZXJ0aWVzLnRyYW5zYWN0aW9uU2FtcGxlUmF0ZSA9IE1hdGgucm91bmQodHJhbnNhY3Rpb25TYW1wbGVSYXRlICogMTAwMDApIC8gMTAwMDA7XG4gICAgfVxuXG4gICAgbWVyZ2UodGhpcy5jb25maWcsIHByb3BlcnRpZXMpO1xuICAgIHRoaXMuZXZlbnRzLnNlbmQoQ09ORklHX0NIQU5HRSwgW3RoaXMuY29uZmlnXSk7XG4gIH07XG5cbiAgX3Byb3RvLnZhbGlkYXRlID0gZnVuY3Rpb24gdmFsaWRhdGUocHJvcGVydGllcykge1xuICAgIGlmIChwcm9wZXJ0aWVzID09PSB2b2lkIDApIHtcbiAgICAgIHByb3BlcnRpZXMgPSB7fTtcbiAgICB9XG5cbiAgICB2YXIgcmVxdWlyZWRLZXlzID0gWydzZXJ2aWNlTmFtZScsICdzZXJ2ZXJVcmwnXTtcbiAgICB2YXIgYWxsS2V5cyA9IE9iamVjdC5rZXlzKHRoaXMuY29uZmlnKTtcbiAgICB2YXIgZXJyb3JzID0ge1xuICAgICAgbWlzc2luZzogW10sXG4gICAgICBpbnZhbGlkOiBbXSxcbiAgICAgIHVua25vd246IFtdXG4gICAgfTtcbiAgICBPYmplY3Qua2V5cyhwcm9wZXJ0aWVzKS5mb3JFYWNoKGZ1bmN0aW9uIChrZXkpIHtcbiAgICAgIGlmIChyZXF1aXJlZEtleXMuaW5kZXhPZihrZXkpICE9PSAtMSAmJiAhcHJvcGVydGllc1trZXldKSB7XG4gICAgICAgIGVycm9ycy5taXNzaW5nLnB1c2goa2V5KTtcbiAgICAgIH1cblxuICAgICAgaWYgKGFsbEtleXMuaW5kZXhPZihrZXkpID09PSAtMSkge1xuICAgICAgICBlcnJvcnMudW5rbm93bi5wdXNoKGtleSk7XG4gICAgICB9XG4gICAgfSk7XG5cbiAgICBpZiAocHJvcGVydGllcy5zZXJ2aWNlTmFtZSAmJiAhL15bYS16QS1aMC05IF8tXSskLy50ZXN0KHByb3BlcnRpZXMuc2VydmljZU5hbWUpKSB7XG4gICAgICBlcnJvcnMuaW52YWxpZC5wdXNoKHtcbiAgICAgICAga2V5OiAnc2VydmljZU5hbWUnLFxuICAgICAgICB2YWx1ZTogcHJvcGVydGllcy5zZXJ2aWNlTmFtZSxcbiAgICAgICAgYWxsb3dlZDogJ2EteiwgQS1aLCAwLTksIF8sIC0sIDxzcGFjZT4nXG4gICAgICB9KTtcbiAgICB9XG5cbiAgICB2YXIgc2FtcGxlUmF0ZSA9IHByb3BlcnRpZXMudHJhbnNhY3Rpb25TYW1wbGVSYXRlO1xuXG4gICAgaWYgKHR5cGVvZiBzYW1wbGVSYXRlICE9PSAndW5kZWZpbmVkJyAmJiAodHlwZW9mIHNhbXBsZVJhdGUgIT09ICdudW1iZXInIHx8IGlzTmFOKHNhbXBsZVJhdGUpIHx8IHNhbXBsZVJhdGUgPCAwIHx8IHNhbXBsZVJhdGUgPiAxKSkge1xuICAgICAgZXJyb3JzLmludmFsaWQucHVzaCh7XG4gICAgICAgIGtleTogJ3RyYW5zYWN0aW9uU2FtcGxlUmF0ZScsXG4gICAgICAgIHZhbHVlOiBzYW1wbGVSYXRlLFxuICAgICAgICBhbGxvd2VkOiAnTnVtYmVyIGJldHdlZW4gMCBhbmQgMSdcbiAgICAgIH0pO1xuICAgIH1cblxuICAgIHJldHVybiBlcnJvcnM7XG4gIH07XG5cbiAgX3Byb3RvLmdldExvY2FsQ29uZmlnID0gZnVuY3Rpb24gZ2V0TG9jYWxDb25maWcoKSB7XG4gICAgdmFyIHN0b3JhZ2UgPSBzZXNzaW9uU3RvcmFnZTtcblxuICAgIGlmICh0aGlzLmNvbmZpZy5zZXNzaW9uKSB7XG4gICAgICBzdG9yYWdlID0gbG9jYWxTdG9yYWdlO1xuICAgIH1cblxuICAgIHZhciBjb25maWcgPSBzdG9yYWdlLmdldEl0ZW0oTE9DQUxfQ09ORklHX0tFWSk7XG5cbiAgICBpZiAoY29uZmlnKSB7XG4gICAgICByZXR1cm4gSlNPTi5wYXJzZShjb25maWcpO1xuICAgIH1cbiAgfTtcblxuICBfcHJvdG8uc2V0TG9jYWxDb25maWcgPSBmdW5jdGlvbiBzZXRMb2NhbENvbmZpZyhjb25maWcsIG1lcmdlKSB7XG4gICAgaWYgKGNvbmZpZykge1xuICAgICAgaWYgKG1lcmdlKSB7XG4gICAgICAgIHZhciBwcmV2Q29uZmlnID0gdGhpcy5nZXRMb2NhbENvbmZpZygpO1xuICAgICAgICBjb25maWcgPSBfZXh0ZW5kcyh7fSwgcHJldkNvbmZpZywgY29uZmlnKTtcbiAgICAgIH1cblxuICAgICAgdmFyIHN0b3JhZ2UgPSBzZXNzaW9uU3RvcmFnZTtcblxuICAgICAgaWYgKHRoaXMuY29uZmlnLnNlc3Npb24pIHtcbiAgICAgICAgc3RvcmFnZSA9IGxvY2FsU3RvcmFnZTtcbiAgICAgIH1cblxuICAgICAgc3RvcmFnZS5zZXRJdGVtKExPQ0FMX0NPTkZJR19LRVksIEpTT04uc3RyaW5naWZ5KGNvbmZpZykpO1xuICAgIH1cbiAgfTtcblxuICBfcHJvdG8uZGlzcGF0Y2hFdmVudCA9IGZ1bmN0aW9uIGRpc3BhdGNoRXZlbnQobmFtZSwgYXJncykge1xuICAgIHRoaXMuZXZlbnRzLnNlbmQobmFtZSwgYXJncyk7XG4gIH07XG5cbiAgX3Byb3RvLm9ic2VydmVFdmVudCA9IGZ1bmN0aW9uIG9ic2VydmVFdmVudChuYW1lLCBmbikge1xuICAgIHJldHVybiB0aGlzLmV2ZW50cy5vYnNlcnZlKG5hbWUsIGZuKTtcbiAgfTtcblxuICByZXR1cm4gQ29uZmlnO1xufSgpO1xuXG5leHBvcnQgZGVmYXVsdCBDb25maWc7IiwidmFyIFNDSEVEVUxFID0gJ3NjaGVkdWxlJztcbnZhciBJTlZPS0UgPSAnaW52b2tlJztcbnZhciBBRERfRVZFTlRfTElTVEVORVJfU1RSID0gJ2FkZEV2ZW50TGlzdGVuZXInO1xudmFyIFJFTU9WRV9FVkVOVF9MSVNURU5FUl9TVFIgPSAncmVtb3ZlRXZlbnRMaXN0ZW5lcic7XG52YXIgUkVTT1VSQ0VfSU5JVElBVE9SX1RZUEVTID0gWydsaW5rJywgJ2NzcycsICdzY3JpcHQnLCAnaW1nJywgJ3htbGh0dHByZXF1ZXN0JywgJ2ZldGNoJywgJ2JlYWNvbicsICdpZnJhbWUnXTtcbnZhciBSRVVTQUJJTElUWV9USFJFU0hPTEQgPSA1MDAwO1xudmFyIE1BWF9TUEFOX0RVUkFUSU9OID0gNSAqIDYwICogMTAwMDtcbnZhciBQQUdFX0xPQURfREVMQVkgPSAxMDAwO1xudmFyIFBBR0VfTE9BRCA9ICdwYWdlLWxvYWQnO1xudmFyIFJPVVRFX0NIQU5HRSA9ICdyb3V0ZS1jaGFuZ2UnO1xudmFyIFRZUEVfQ1VTVE9NID0gJ2N1c3RvbSc7XG52YXIgVVNFUl9JTlRFUkFDVElPTiA9ICd1c2VyLWludGVyYWN0aW9uJztcbnZhciBIVFRQX1JFUVVFU1RfVFlQRSA9ICdodHRwLXJlcXVlc3QnO1xudmFyIFRFTVBPUkFSWV9UWVBFID0gJ3RlbXBvcmFyeSc7XG52YXIgTkFNRV9VTktOT1dOID0gJ1Vua25vd24nO1xudmFyIFRSQU5TQUNUSU9OX1RZUEVfT1JERVIgPSBbUEFHRV9MT0FELCBST1VURV9DSEFOR0UsIFVTRVJfSU5URVJBQ1RJT04sIEhUVFBfUkVRVUVTVF9UWVBFLCBUWVBFX0NVU1RPTSwgVEVNUE9SQVJZX1RZUEVdO1xudmFyIE9VVENPTUVfU1VDQ0VTUyA9ICdzdWNjZXNzJztcbnZhciBPVVRDT01FX0ZBSUxVUkUgPSAnZmFpbHVyZSc7XG52YXIgT1VUQ09NRV9VTktOT1dOID0gJ3Vua25vd24nO1xudmFyIFVTRVJfVElNSU5HX1RIUkVTSE9MRCA9IDYwO1xudmFyIFRSQU5TQUNUSU9OX1NUQVJUID0gJ3RyYW5zYWN0aW9uOnN0YXJ0JztcbnZhciBUUkFOU0FDVElPTl9FTkQgPSAndHJhbnNhY3Rpb246ZW5kJztcbnZhciBDT05GSUdfQ0hBTkdFID0gJ2NvbmZpZzpjaGFuZ2UnO1xudmFyIFFVRVVFX0ZMVVNIID0gJ3F1ZXVlOmZsdXNoJztcbnZhciBRVUVVRV9BRERfVFJBTlNBQ1RJT04gPSAncXVldWU6YWRkX3RyYW5zYWN0aW9uJztcbnZhciBYTUxIVFRQUkVRVUVTVCA9ICd4bWxodHRwcmVxdWVzdCc7XG52YXIgRkVUQ0ggPSAnZmV0Y2gnO1xudmFyIEhJU1RPUlkgPSAnaGlzdG9yeSc7XG52YXIgRVZFTlRfVEFSR0VUID0gJ2V2ZW50dGFyZ2V0JztcbnZhciBDTElDSyA9ICdjbGljayc7XG52YXIgRVJST1IgPSAnZXJyb3InO1xudmFyIEJFRk9SRV9FVkVOVCA9ICc6YmVmb3JlJztcbnZhciBBRlRFUl9FVkVOVCA9ICc6YWZ0ZXInO1xudmFyIExPQ0FMX0NPTkZJR19LRVkgPSAnZWxhc3RpY19hcG1fY29uZmlnJztcbnZhciBMT05HX1RBU0sgPSAnbG9uZ3Rhc2snO1xudmFyIFBBSU5UID0gJ3BhaW50JztcbnZhciBNRUFTVVJFID0gJ21lYXN1cmUnO1xudmFyIE5BVklHQVRJT04gPSAnbmF2aWdhdGlvbic7XG52YXIgUkVTT1VSQ0UgPSAncmVzb3VyY2UnO1xudmFyIEZJUlNUX0NPTlRFTlRGVUxfUEFJTlQgPSAnZmlyc3QtY29udGVudGZ1bC1wYWludCc7XG52YXIgTEFSR0VTVF9DT05URU5URlVMX1BBSU5UID0gJ2xhcmdlc3QtY29udGVudGZ1bC1wYWludCc7XG52YXIgRklSU1RfSU5QVVQgPSAnZmlyc3QtaW5wdXQnO1xudmFyIExBWU9VVF9TSElGVCA9ICdsYXlvdXQtc2hpZnQnO1xudmFyIEVSUk9SUyA9ICdlcnJvcnMnO1xudmFyIFRSQU5TQUNUSU9OUyA9ICd0cmFuc2FjdGlvbnMnO1xudmFyIENPTkZJR19TRVJWSUNFID0gJ0NvbmZpZ1NlcnZpY2UnO1xudmFyIExPR0dJTkdfU0VSVklDRSA9ICdMb2dnaW5nU2VydmljZSc7XG52YXIgVFJBTlNBQ1RJT05fU0VSVklDRSA9ICdUcmFuc2FjdGlvblNlcnZpY2UnO1xudmFyIEFQTV9TRVJWRVIgPSAnQXBtU2VydmVyJztcbnZhciBQRVJGT1JNQU5DRV9NT05JVE9SSU5HID0gJ1BlcmZvcm1hbmNlTW9uaXRvcmluZyc7XG52YXIgRVJST1JfTE9HR0lORyA9ICdFcnJvckxvZ2dpbmcnO1xudmFyIFRSVU5DQVRFRF9UWVBFID0gJy50cnVuY2F0ZWQnO1xudmFyIEtFWVdPUkRfTElNSVQgPSAxMDI0O1xudmFyIFNFU1NJT05fVElNRU9VVCA9IDMwICogNjAwMDA7XG52YXIgSFRUUF9SRVFVRVNUX1RJTUVPVVQgPSAxMDAwMDtcbmV4cG9ydCB7IFNDSEVEVUxFLCBJTlZPS0UsIEFERF9FVkVOVF9MSVNURU5FUl9TVFIsIFJFTU9WRV9FVkVOVF9MSVNURU5FUl9TVFIsIFJFU09VUkNFX0lOSVRJQVRPUl9UWVBFUywgUkVVU0FCSUxJVFlfVEhSRVNIT0xELCBNQVhfU1BBTl9EVVJBVElPTiwgUEFHRV9MT0FEX0RFTEFZLCBQQUdFX0xPQUQsIFJPVVRFX0NIQU5HRSwgTkFNRV9VTktOT1dOLCBUWVBFX0NVU1RPTSwgVVNFUl9USU1JTkdfVEhSRVNIT0xELCBUUkFOU0FDVElPTl9TVEFSVCwgVFJBTlNBQ1RJT05fRU5ELCBDT05GSUdfQ0hBTkdFLCBRVUVVRV9GTFVTSCwgUVVFVUVfQUREX1RSQU5TQUNUSU9OLCBYTUxIVFRQUkVRVUVTVCwgRkVUQ0gsIEhJU1RPUlksIEVWRU5UX1RBUkdFVCwgQ0xJQ0ssIEVSUk9SLCBCRUZPUkVfRVZFTlQsIEFGVEVSX0VWRU5ULCBMT0NBTF9DT05GSUdfS0VZLCBIVFRQX1JFUVVFU1RfVFlQRSwgTE9OR19UQVNLLCBQQUlOVCwgTUVBU1VSRSwgTkFWSUdBVElPTiwgUkVTT1VSQ0UsIEZJUlNUX0NPTlRFTlRGVUxfUEFJTlQsIExBUkdFU1RfQ09OVEVOVEZVTF9QQUlOVCwgS0VZV09SRF9MSU1JVCwgVEVNUE9SQVJZX1RZUEUsIFVTRVJfSU5URVJBQ1RJT04sIFRSQU5TQUNUSU9OX1RZUEVfT1JERVIsIEVSUk9SUywgVFJBTlNBQ1RJT05TLCBDT05GSUdfU0VSVklDRSwgTE9HR0lOR19TRVJWSUNFLCBUUkFOU0FDVElPTl9TRVJWSUNFLCBBUE1fU0VSVkVSLCBQRVJGT1JNQU5DRV9NT05JVE9SSU5HLCBFUlJPUl9MT0dHSU5HLCBUUlVOQ0FURURfVFlQRSwgRklSU1RfSU5QVVQsIExBWU9VVF9TSElGVCwgT1VUQ09NRV9TVUNDRVNTLCBPVVRDT01FX0ZBSUxVUkUsIE9VVENPTUVfVU5LTk9XTiwgU0VTU0lPTl9USU1FT1VULCBIVFRQX1JFUVVFU1RfVElNRU9VVCB9OyIsInZhciBfZXhjbHVkZWQgPSBbXCJ0YWdzXCJdO1xuXG5mdW5jdGlvbiBfb2JqZWN0V2l0aG91dFByb3BlcnRpZXNMb29zZShzb3VyY2UsIGV4Y2x1ZGVkKSB7IGlmIChzb3VyY2UgPT0gbnVsbCkgcmV0dXJuIHt9OyB2YXIgdGFyZ2V0ID0ge307IHZhciBzb3VyY2VLZXlzID0gT2JqZWN0LmtleXMoc291cmNlKTsgdmFyIGtleSwgaTsgZm9yIChpID0gMDsgaSA8IHNvdXJjZUtleXMubGVuZ3RoOyBpKyspIHsga2V5ID0gc291cmNlS2V5c1tpXTsgaWYgKGV4Y2x1ZGVkLmluZGV4T2Yoa2V5KSA+PSAwKSBjb250aW51ZTsgdGFyZ2V0W2tleV0gPSBzb3VyY2Vba2V5XTsgfSByZXR1cm4gdGFyZ2V0OyB9XG5cbmltcG9ydCB7IFVybCB9IGZyb20gJy4vdXJsJztcbmltcG9ydCB7IFBBR0VfTE9BRCwgTkFWSUdBVElPTiB9IGZyb20gJy4vY29uc3RhbnRzJztcbmltcG9ydCB7IGdldFNlcnZlclRpbWluZ0luZm8sIFBFUkYsIGlzUGVyZlRpbWVsaW5lU3VwcG9ydGVkIH0gZnJvbSAnLi91dGlscyc7XG52YXIgTEVGVF9TUVVBUkVfQlJBQ0tFVCA9IDkxO1xudmFyIFJJR0hUX1NRVUFSRV9CUkFDS0VUID0gOTM7XG52YXIgRVhURVJOQUwgPSAnZXh0ZXJuYWwnO1xudmFyIFJFU09VUkNFID0gJ3Jlc291cmNlJztcbnZhciBIQVJEX05BVklHQVRJT04gPSAnaGFyZC1uYXZpZ2F0aW9uJztcblxuZnVuY3Rpb24gZ2V0UG9ydE51bWJlcihwb3J0LCBwcm90b2NvbCkge1xuICBpZiAocG9ydCA9PT0gJycpIHtcbiAgICBwb3J0ID0gcHJvdG9jb2wgPT09ICdodHRwOicgPyAnODAnIDogcHJvdG9jb2wgPT09ICdodHRwczonID8gJzQ0MycgOiAnJztcbiAgfVxuXG4gIHJldHVybiBwb3J0O1xufVxuXG5mdW5jdGlvbiBnZXRSZXNwb25zZUNvbnRleHQocGVyZlRpbWluZ0VudHJ5KSB7XG4gIHZhciB0cmFuc2ZlclNpemUgPSBwZXJmVGltaW5nRW50cnkudHJhbnNmZXJTaXplLFxuICAgICAgZW5jb2RlZEJvZHlTaXplID0gcGVyZlRpbWluZ0VudHJ5LmVuY29kZWRCb2R5U2l6ZSxcbiAgICAgIGRlY29kZWRCb2R5U2l6ZSA9IHBlcmZUaW1pbmdFbnRyeS5kZWNvZGVkQm9keVNpemUsXG4gICAgICBzZXJ2ZXJUaW1pbmcgPSBwZXJmVGltaW5nRW50cnkuc2VydmVyVGltaW5nO1xuICB2YXIgcmVzcENvbnRleHQgPSB7XG4gICAgdHJhbnNmZXJfc2l6ZTogdHJhbnNmZXJTaXplLFxuICAgIGVuY29kZWRfYm9keV9zaXplOiBlbmNvZGVkQm9keVNpemUsXG4gICAgZGVjb2RlZF9ib2R5X3NpemU6IGRlY29kZWRCb2R5U2l6ZVxuICB9O1xuICB2YXIgc2VydmVyVGltaW5nU3RyID0gZ2V0U2VydmVyVGltaW5nSW5mbyhzZXJ2ZXJUaW1pbmcpO1xuXG4gIGlmIChzZXJ2ZXJUaW1pbmdTdHIpIHtcbiAgICByZXNwQ29udGV4dC5oZWFkZXJzID0ge1xuICAgICAgJ3NlcnZlci10aW1pbmcnOiBzZXJ2ZXJUaW1pbmdTdHJcbiAgICB9O1xuICB9XG5cbiAgcmV0dXJuIHJlc3BDb250ZXh0O1xufVxuXG5mdW5jdGlvbiBnZXREZXN0aW5hdGlvbihwYXJzZWRVcmwpIHtcbiAgdmFyIHBvcnQgPSBwYXJzZWRVcmwucG9ydCxcbiAgICAgIHByb3RvY29sID0gcGFyc2VkVXJsLnByb3RvY29sLFxuICAgICAgaG9zdG5hbWUgPSBwYXJzZWRVcmwuaG9zdG5hbWU7XG4gIHZhciBwb3J0TnVtYmVyID0gZ2V0UG9ydE51bWJlcihwb3J0LCBwcm90b2NvbCk7XG4gIHZhciBpcHY2SG9zdG5hbWUgPSBob3N0bmFtZS5jaGFyQ29kZUF0KDApID09PSBMRUZUX1NRVUFSRV9CUkFDS0VUICYmIGhvc3RuYW1lLmNoYXJDb2RlQXQoaG9zdG5hbWUubGVuZ3RoIC0gMSkgPT09IFJJR0hUX1NRVUFSRV9CUkFDS0VUO1xuICB2YXIgYWRkcmVzcyA9IGhvc3RuYW1lO1xuXG4gIGlmIChpcHY2SG9zdG5hbWUpIHtcbiAgICBhZGRyZXNzID0gaG9zdG5hbWUuc2xpY2UoMSwgLTEpO1xuICB9XG5cbiAgcmV0dXJuIHtcbiAgICBzZXJ2aWNlOiB7XG4gICAgICByZXNvdXJjZTogaG9zdG5hbWUgKyAnOicgKyBwb3J0TnVtYmVyLFxuICAgICAgbmFtZTogJycsXG4gICAgICB0eXBlOiAnJ1xuICAgIH0sXG4gICAgYWRkcmVzczogYWRkcmVzcyxcbiAgICBwb3J0OiBOdW1iZXIocG9ydE51bWJlcilcbiAgfTtcbn1cblxuZnVuY3Rpb24gZ2V0UmVzb3VyY2VDb250ZXh0KGRhdGEpIHtcbiAgdmFyIGVudHJ5ID0gZGF0YS5lbnRyeSxcbiAgICAgIHVybCA9IGRhdGEudXJsO1xuICB2YXIgcGFyc2VkVXJsID0gbmV3IFVybCh1cmwpO1xuICB2YXIgZGVzdGluYXRpb24gPSBnZXREZXN0aW5hdGlvbihwYXJzZWRVcmwpO1xuICByZXR1cm4ge1xuICAgIGh0dHA6IHtcbiAgICAgIHVybDogdXJsLFxuICAgICAgcmVzcG9uc2U6IGdldFJlc3BvbnNlQ29udGV4dChlbnRyeSlcbiAgICB9LFxuICAgIGRlc3RpbmF0aW9uOiBkZXN0aW5hdGlvblxuICB9O1xufVxuXG5mdW5jdGlvbiBnZXRFeHRlcm5hbENvbnRleHQoZGF0YSkge1xuICB2YXIgdXJsID0gZGF0YS51cmwsXG4gICAgICBtZXRob2QgPSBkYXRhLm1ldGhvZCxcbiAgICAgIHRhcmdldCA9IGRhdGEudGFyZ2V0LFxuICAgICAgcmVzcG9uc2UgPSBkYXRhLnJlc3BvbnNlO1xuICB2YXIgcGFyc2VkVXJsID0gbmV3IFVybCh1cmwpO1xuICB2YXIgZGVzdGluYXRpb24gPSBnZXREZXN0aW5hdGlvbihwYXJzZWRVcmwpO1xuICB2YXIgY29udGV4dCA9IHtcbiAgICBodHRwOiB7XG4gICAgICBtZXRob2Q6IG1ldGhvZCxcbiAgICAgIHVybDogcGFyc2VkVXJsLmhyZWZcbiAgICB9LFxuICAgIGRlc3RpbmF0aW9uOiBkZXN0aW5hdGlvblxuICB9O1xuICB2YXIgc3RhdHVzQ29kZTtcblxuICBpZiAodGFyZ2V0ICYmIHR5cGVvZiB0YXJnZXQuc3RhdHVzICE9PSAndW5kZWZpbmVkJykge1xuICAgIHN0YXR1c0NvZGUgPSB0YXJnZXQuc3RhdHVzO1xuICB9IGVsc2UgaWYgKHJlc3BvbnNlKSB7XG4gICAgc3RhdHVzQ29kZSA9IHJlc3BvbnNlLnN0YXR1cztcbiAgfVxuXG4gIGNvbnRleHQuaHR0cC5zdGF0dXNfY29kZSA9IHN0YXR1c0NvZGU7XG4gIHJldHVybiBjb250ZXh0O1xufVxuXG5mdW5jdGlvbiBnZXROYXZpZ2F0aW9uQ29udGV4dChkYXRhKSB7XG4gIHZhciB1cmwgPSBkYXRhLnVybDtcbiAgdmFyIHBhcnNlZFVybCA9IG5ldyBVcmwodXJsKTtcbiAgdmFyIGRlc3RpbmF0aW9uID0gZ2V0RGVzdGluYXRpb24ocGFyc2VkVXJsKTtcbiAgcmV0dXJuIHtcbiAgICBkZXN0aW5hdGlvbjogZGVzdGluYXRpb25cbiAgfTtcbn1cblxuZXhwb3J0IGZ1bmN0aW9uIGdldFBhZ2VDb250ZXh0KCkge1xuICByZXR1cm4ge1xuICAgIHBhZ2U6IHtcbiAgICAgIHJlZmVyZXI6IGRvY3VtZW50LnJlZmVycmVyLFxuICAgICAgdXJsOiBsb2NhdGlvbi5ocmVmXG4gICAgfVxuICB9O1xufVxuZXhwb3J0IGZ1bmN0aW9uIGFkZFNwYW5Db250ZXh0KHNwYW4sIGRhdGEpIHtcbiAgaWYgKCFkYXRhKSB7XG4gICAgcmV0dXJuO1xuICB9XG5cbiAgdmFyIHR5cGUgPSBzcGFuLnR5cGU7XG4gIHZhciBjb250ZXh0O1xuXG4gIHN3aXRjaCAodHlwZSkge1xuICAgIGNhc2UgRVhURVJOQUw6XG4gICAgICBjb250ZXh0ID0gZ2V0RXh0ZXJuYWxDb250ZXh0KGRhdGEpO1xuICAgICAgYnJlYWs7XG5cbiAgICBjYXNlIFJFU09VUkNFOlxuICAgICAgY29udGV4dCA9IGdldFJlc291cmNlQ29udGV4dChkYXRhKTtcbiAgICAgIGJyZWFrO1xuXG4gICAgY2FzZSBIQVJEX05BVklHQVRJT046XG4gICAgICBjb250ZXh0ID0gZ2V0TmF2aWdhdGlvbkNvbnRleHQoZGF0YSk7XG4gICAgICBicmVhaztcbiAgfVxuXG4gIHNwYW4uYWRkQ29udGV4dChjb250ZXh0KTtcbn1cbmV4cG9ydCBmdW5jdGlvbiBhZGRUcmFuc2FjdGlvbkNvbnRleHQodHJhbnNhY3Rpb24sIF90ZW1wKSB7XG4gIHZhciBfcmVmID0gX3RlbXAgPT09IHZvaWQgMCA/IHt9IDogX3RlbXAsXG4gICAgICB0YWdzID0gX3JlZi50YWdzLFxuICAgICAgY29uZmlnQ29udGV4dCA9IF9vYmplY3RXaXRob3V0UHJvcGVydGllc0xvb3NlKF9yZWYsIF9leGNsdWRlZCk7XG5cbiAgdmFyIHBhZ2VDb250ZXh0ID0gZ2V0UGFnZUNvbnRleHQoKTtcbiAgdmFyIHJlc3BvbnNlQ29udGV4dCA9IHt9O1xuXG4gIGlmICh0cmFuc2FjdGlvbi50eXBlID09PSBQQUdFX0xPQUQgJiYgaXNQZXJmVGltZWxpbmVTdXBwb3J0ZWQoKSkge1xuICAgIHZhciBlbnRyaWVzID0gUEVSRi5nZXRFbnRyaWVzQnlUeXBlKE5BVklHQVRJT04pO1xuXG4gICAgaWYgKGVudHJpZXMgJiYgZW50cmllcy5sZW5ndGggPiAwKSB7XG4gICAgICByZXNwb25zZUNvbnRleHQgPSB7XG4gICAgICAgIHJlc3BvbnNlOiBnZXRSZXNwb25zZUNvbnRleHQoZW50cmllc1swXSlcbiAgICAgIH07XG4gICAgfVxuICB9XG5cbiAgdHJhbnNhY3Rpb24uYWRkQ29udGV4dChwYWdlQ29udGV4dCwgcmVzcG9uc2VDb250ZXh0LCBjb25maWdDb250ZXh0KTtcbn0iLCJpbXBvcnQgeyBCRUZPUkVfRVZFTlQsIEFGVEVSX0VWRU5UIH0gZnJvbSAnLi9jb25zdGFudHMnO1xuXG52YXIgRXZlbnRIYW5kbGVyID0gZnVuY3Rpb24gKCkge1xuICBmdW5jdGlvbiBFdmVudEhhbmRsZXIoKSB7XG4gICAgdGhpcy5vYnNlcnZlcnMgPSB7fTtcbiAgfVxuXG4gIHZhciBfcHJvdG8gPSBFdmVudEhhbmRsZXIucHJvdG90eXBlO1xuXG4gIF9wcm90by5vYnNlcnZlID0gZnVuY3Rpb24gb2JzZXJ2ZShuYW1lLCBmbikge1xuICAgIHZhciBfdGhpcyA9IHRoaXM7XG5cbiAgICBpZiAodHlwZW9mIGZuID09PSAnZnVuY3Rpb24nKSB7XG4gICAgICBpZiAoIXRoaXMub2JzZXJ2ZXJzW25hbWVdKSB7XG4gICAgICAgIHRoaXMub2JzZXJ2ZXJzW25hbWVdID0gW107XG4gICAgICB9XG5cbiAgICAgIHRoaXMub2JzZXJ2ZXJzW25hbWVdLnB1c2goZm4pO1xuICAgICAgcmV0dXJuIGZ1bmN0aW9uICgpIHtcbiAgICAgICAgdmFyIGluZGV4ID0gX3RoaXMub2JzZXJ2ZXJzW25hbWVdLmluZGV4T2YoZm4pO1xuXG4gICAgICAgIGlmIChpbmRleCA+IC0xKSB7XG4gICAgICAgICAgX3RoaXMub2JzZXJ2ZXJzW25hbWVdLnNwbGljZShpbmRleCwgMSk7XG4gICAgICAgIH1cbiAgICAgIH07XG4gICAgfVxuICB9O1xuXG4gIF9wcm90by5zZW5kT25seSA9IGZ1bmN0aW9uIHNlbmRPbmx5KG5hbWUsIGFyZ3MpIHtcbiAgICB2YXIgb2JzID0gdGhpcy5vYnNlcnZlcnNbbmFtZV07XG5cbiAgICBpZiAob2JzKSB7XG4gICAgICBvYnMuZm9yRWFjaChmdW5jdGlvbiAoZm4pIHtcbiAgICAgICAgdHJ5IHtcbiAgICAgICAgICBmbi5hcHBseSh1bmRlZmluZWQsIGFyZ3MpO1xuICAgICAgICB9IGNhdGNoIChlcnJvcikge1xuICAgICAgICAgIGNvbnNvbGUubG9nKGVycm9yLCBlcnJvci5zdGFjayk7XG4gICAgICAgIH1cbiAgICAgIH0pO1xuICAgIH1cbiAgfTtcblxuICBfcHJvdG8uc2VuZCA9IGZ1bmN0aW9uIHNlbmQobmFtZSwgYXJncykge1xuICAgIHRoaXMuc2VuZE9ubHkobmFtZSArIEJFRk9SRV9FVkVOVCwgYXJncyk7XG4gICAgdGhpcy5zZW5kT25seShuYW1lLCBhcmdzKTtcbiAgICB0aGlzLnNlbmRPbmx5KG5hbWUgKyBBRlRFUl9FVkVOVCwgYXJncyk7XG4gIH07XG5cbiAgcmV0dXJuIEV2ZW50SGFuZGxlcjtcbn0oKTtcblxuZXhwb3J0IGRlZmF1bHQgRXZlbnRIYW5kbGVyOyIsImZ1bmN0aW9uIF9leHRlbmRzKCkgeyBfZXh0ZW5kcyA9IE9iamVjdC5hc3NpZ24gfHwgZnVuY3Rpb24gKHRhcmdldCkgeyBmb3IgKHZhciBpID0gMTsgaSA8IGFyZ3VtZW50cy5sZW5ndGg7IGkrKykgeyB2YXIgc291cmNlID0gYXJndW1lbnRzW2ldOyBmb3IgKHZhciBrZXkgaW4gc291cmNlKSB7IGlmIChPYmplY3QucHJvdG90eXBlLmhhc093blByb3BlcnR5LmNhbGwoc291cmNlLCBrZXkpKSB7IHRhcmdldFtrZXldID0gc291cmNlW2tleV07IH0gfSB9IHJldHVybiB0YXJnZXQ7IH07IHJldHVybiBfZXh0ZW5kcy5hcHBseSh0aGlzLCBhcmd1bWVudHMpOyB9XG5cbmltcG9ydCB7IEhUVFBfUkVRVUVTVF9USU1FT1VUIH0gZnJvbSAnLi4vY29uc3RhbnRzJztcbmltcG9ydCB7IGlzUmVzcG9uc2VTdWNjZXNzZnVsIH0gZnJvbSAnLi9yZXNwb25zZS1zdGF0dXMnO1xuZXhwb3J0IHZhciBCWVRFX0xJTUlUID0gNjAgKiAxMDAwO1xuZXhwb3J0IGZ1bmN0aW9uIHNob3VsZFVzZUZldGNoV2l0aEtlZXBBbGl2ZShtZXRob2QsIHBheWxvYWQpIHtcbiAgaWYgKCFpc0ZldGNoU3VwcG9ydGVkKCkpIHtcbiAgICByZXR1cm4gZmFsc2U7XG4gIH1cblxuICB2YXIgaXNLZWVwQWxpdmVTdXBwb3J0ZWQgPSAoJ2tlZXBhbGl2ZScgaW4gbmV3IFJlcXVlc3QoJycpKTtcblxuICBpZiAoIWlzS2VlcEFsaXZlU3VwcG9ydGVkKSB7XG4gICAgcmV0dXJuIGZhbHNlO1xuICB9XG5cbiAgdmFyIHNpemUgPSBjYWxjdWxhdGVTaXplKHBheWxvYWQpO1xuICByZXR1cm4gbWV0aG9kID09PSAnUE9TVCcgJiYgc2l6ZSA8IEJZVEVfTElNSVQ7XG59XG5leHBvcnQgZnVuY3Rpb24gc2VuZEZldGNoUmVxdWVzdChtZXRob2QsIHVybCwgX3JlZikge1xuICB2YXIgX3JlZiRrZWVwYWxpdmUgPSBfcmVmLmtlZXBhbGl2ZSxcbiAgICAgIGtlZXBhbGl2ZSA9IF9yZWYka2VlcGFsaXZlID09PSB2b2lkIDAgPyBmYWxzZSA6IF9yZWYka2VlcGFsaXZlLFxuICAgICAgX3JlZiR0aW1lb3V0ID0gX3JlZi50aW1lb3V0LFxuICAgICAgdGltZW91dCA9IF9yZWYkdGltZW91dCA9PT0gdm9pZCAwID8gSFRUUF9SRVFVRVNUX1RJTUVPVVQgOiBfcmVmJHRpbWVvdXQsXG4gICAgICBwYXlsb2FkID0gX3JlZi5wYXlsb2FkLFxuICAgICAgaGVhZGVycyA9IF9yZWYuaGVhZGVycyxcbiAgICAgIHNlbmRDcmVkZW50aWFscyA9IF9yZWYuc2VuZENyZWRlbnRpYWxzO1xuICB2YXIgdGltZW91dENvbmZpZyA9IHt9O1xuXG4gIGlmICh0eXBlb2YgQWJvcnRDb250cm9sbGVyID09PSAnZnVuY3Rpb24nKSB7XG4gICAgdmFyIGNvbnRyb2xsZXIgPSBuZXcgQWJvcnRDb250cm9sbGVyKCk7XG4gICAgdGltZW91dENvbmZpZy5zaWduYWwgPSBjb250cm9sbGVyLnNpZ25hbDtcbiAgICBzZXRUaW1lb3V0KGZ1bmN0aW9uICgpIHtcbiAgICAgIHJldHVybiBjb250cm9sbGVyLmFib3J0KCk7XG4gICAgfSwgdGltZW91dCk7XG4gIH1cblxuICB2YXIgZmV0Y2hSZXNwb25zZTtcbiAgcmV0dXJuIHdpbmRvdy5mZXRjaCh1cmwsIF9leHRlbmRzKHtcbiAgICBib2R5OiBwYXlsb2FkLFxuICAgIGhlYWRlcnM6IGhlYWRlcnMsXG4gICAgbWV0aG9kOiBtZXRob2QsXG4gICAga2VlcGFsaXZlOiBrZWVwYWxpdmUsXG4gICAgY3JlZGVudGlhbHM6IHNlbmRDcmVkZW50aWFscyA/ICdpbmNsdWRlJyA6ICdvbWl0J1xuICB9LCB0aW1lb3V0Q29uZmlnKSkudGhlbihmdW5jdGlvbiAocmVzcG9uc2UpIHtcbiAgICBmZXRjaFJlc3BvbnNlID0gcmVzcG9uc2U7XG4gICAgcmV0dXJuIGZldGNoUmVzcG9uc2UudGV4dCgpO1xuICB9KS50aGVuKGZ1bmN0aW9uIChyZXNwb25zZVRleHQpIHtcbiAgICB2YXIgYm9keVJlc3BvbnNlID0ge1xuICAgICAgdXJsOiB1cmwsXG4gICAgICBzdGF0dXM6IGZldGNoUmVzcG9uc2Uuc3RhdHVzLFxuICAgICAgcmVzcG9uc2VUZXh0OiByZXNwb25zZVRleHRcbiAgICB9O1xuXG4gICAgaWYgKCFpc1Jlc3BvbnNlU3VjY2Vzc2Z1bChmZXRjaFJlc3BvbnNlLnN0YXR1cykpIHtcbiAgICAgIHRocm93IGJvZHlSZXNwb25zZTtcbiAgICB9XG5cbiAgICByZXR1cm4gYm9keVJlc3BvbnNlO1xuICB9KTtcbn1cbmV4cG9ydCBmdW5jdGlvbiBpc0ZldGNoU3VwcG9ydGVkKCkge1xuICByZXR1cm4gdHlwZW9mIHdpbmRvdy5mZXRjaCA9PT0gJ2Z1bmN0aW9uJyAmJiB0eXBlb2Ygd2luZG93LlJlcXVlc3QgPT09ICdmdW5jdGlvbic7XG59XG5cbmZ1bmN0aW9uIGNhbGN1bGF0ZVNpemUocGF5bG9hZCkge1xuICBpZiAoIXBheWxvYWQpIHtcbiAgICByZXR1cm4gMDtcbiAgfVxuXG4gIGlmIChwYXlsb2FkIGluc3RhbmNlb2YgQmxvYikge1xuICAgIHJldHVybiBwYXlsb2FkLnNpemU7XG4gIH1cblxuICByZXR1cm4gbmV3IEJsb2IoW3BheWxvYWRdKS5zaXplO1xufSIsImV4cG9ydCBmdW5jdGlvbiBpc1Jlc3BvbnNlU3VjY2Vzc2Z1bChzdGF0dXMpIHtcbiAgaWYgKHN0YXR1cyA9PT0gMCB8fCBzdGF0dXMgPiAzOTkgJiYgc3RhdHVzIDwgNjAwKSB7XG4gICAgcmV0dXJuIGZhbHNlO1xuICB9XG5cbiAgcmV0dXJuIHRydWU7XG59IiwiaW1wb3J0IHsgWEhSX0lHTk9SRSB9IGZyb20gJy4uL3BhdGNoaW5nL3BhdGNoLXV0aWxzJztcbmltcG9ydCB7IGlzUmVzcG9uc2VTdWNjZXNzZnVsIH0gZnJvbSAnLi9yZXNwb25zZS1zdGF0dXMnO1xuaW1wb3J0IHsgUHJvbWlzZSB9IGZyb20gJy4uL3BvbHlmaWxscyc7XG5leHBvcnQgZnVuY3Rpb24gc2VuZFhIUihtZXRob2QsIHVybCwgX3JlZikge1xuICB2YXIgX3JlZiR0aW1lb3V0ID0gX3JlZi50aW1lb3V0LFxuICAgICAgdGltZW91dCA9IF9yZWYkdGltZW91dCA9PT0gdm9pZCAwID8gSFRUUF9SRVFVRVNUX1RJTUVPVVQgOiBfcmVmJHRpbWVvdXQsXG4gICAgICBwYXlsb2FkID0gX3JlZi5wYXlsb2FkLFxuICAgICAgaGVhZGVycyA9IF9yZWYuaGVhZGVycyxcbiAgICAgIGJlZm9yZVNlbmQgPSBfcmVmLmJlZm9yZVNlbmQsXG4gICAgICBzZW5kQ3JlZGVudGlhbHMgPSBfcmVmLnNlbmRDcmVkZW50aWFscztcbiAgcmV0dXJuIG5ldyBQcm9taXNlKGZ1bmN0aW9uIChyZXNvbHZlLCByZWplY3QpIHtcbiAgICB2YXIgeGhyID0gbmV3IHdpbmRvdy5YTUxIdHRwUmVxdWVzdCgpO1xuICAgIHhocltYSFJfSUdOT1JFXSA9IHRydWU7XG4gICAgeGhyLm9wZW4obWV0aG9kLCB1cmwsIHRydWUpO1xuICAgIHhoci50aW1lb3V0ID0gdGltZW91dDtcbiAgICB4aHIud2l0aENyZWRlbnRpYWxzID0gc2VuZENyZWRlbnRpYWxzO1xuXG4gICAgaWYgKGhlYWRlcnMpIHtcbiAgICAgIGZvciAodmFyIGhlYWRlciBpbiBoZWFkZXJzKSB7XG4gICAgICAgIGlmIChoZWFkZXJzLmhhc093blByb3BlcnR5KGhlYWRlcikpIHtcbiAgICAgICAgICB4aHIuc2V0UmVxdWVzdEhlYWRlcihoZWFkZXIsIGhlYWRlcnNbaGVhZGVyXSk7XG4gICAgICAgIH1cbiAgICAgIH1cbiAgICB9XG5cbiAgICB4aHIub25yZWFkeXN0YXRlY2hhbmdlID0gZnVuY3Rpb24gKCkge1xuICAgICAgaWYgKHhoci5yZWFkeVN0YXRlID09PSA0KSB7XG4gICAgICAgIHZhciBzdGF0dXMgPSB4aHIuc3RhdHVzLFxuICAgICAgICAgICAgcmVzcG9uc2VUZXh0ID0geGhyLnJlc3BvbnNlVGV4dDtcblxuICAgICAgICBpZiAoaXNSZXNwb25zZVN1Y2Nlc3NmdWwoc3RhdHVzKSkge1xuICAgICAgICAgIHJlc29sdmUoeGhyKTtcbiAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICByZWplY3Qoe1xuICAgICAgICAgICAgdXJsOiB1cmwsXG4gICAgICAgICAgICBzdGF0dXM6IHN0YXR1cyxcbiAgICAgICAgICAgIHJlc3BvbnNlVGV4dDogcmVzcG9uc2VUZXh0XG4gICAgICAgICAgfSk7XG4gICAgICAgIH1cbiAgICAgIH1cbiAgICB9O1xuXG4gICAgeGhyLm9uZXJyb3IgPSBmdW5jdGlvbiAoKSB7XG4gICAgICB2YXIgc3RhdHVzID0geGhyLnN0YXR1cyxcbiAgICAgICAgICByZXNwb25zZVRleHQgPSB4aHIucmVzcG9uc2VUZXh0O1xuICAgICAgcmVqZWN0KHtcbiAgICAgICAgdXJsOiB1cmwsXG4gICAgICAgIHN0YXR1czogc3RhdHVzLFxuICAgICAgICByZXNwb25zZVRleHQ6IHJlc3BvbnNlVGV4dFxuICAgICAgfSk7XG4gICAgfTtcblxuICAgIHZhciBjYW5TZW5kID0gdHJ1ZTtcblxuICAgIGlmICh0eXBlb2YgYmVmb3JlU2VuZCA9PT0gJ2Z1bmN0aW9uJykge1xuICAgICAgY2FuU2VuZCA9IGJlZm9yZVNlbmQoe1xuICAgICAgICB1cmw6IHVybCxcbiAgICAgICAgbWV0aG9kOiBtZXRob2QsXG4gICAgICAgIGhlYWRlcnM6IGhlYWRlcnMsXG4gICAgICAgIHBheWxvYWQ6IHBheWxvYWQsXG4gICAgICAgIHhocjogeGhyXG4gICAgICB9KTtcbiAgICB9XG5cbiAgICBpZiAoY2FuU2VuZCkge1xuICAgICAgeGhyLnNlbmQocGF5bG9hZCk7XG4gICAgfSBlbHNlIHtcbiAgICAgIHJlamVjdCh7XG4gICAgICAgIHVybDogdXJsLFxuICAgICAgICBzdGF0dXM6IDAsXG4gICAgICAgIHJlc3BvbnNlVGV4dDogJ1JlcXVlc3QgcmVqZWN0ZWQgYnkgdXNlciBjb25maWd1cmF0aW9uLidcbiAgICAgIH0pO1xuICAgIH1cbiAgfSk7XG59IiwiaW1wb3J0IHsgWE1MSFRUUFJFUVVFU1QsIEZFVENILCBISVNUT1JZLCBQQUdFX0xPQUQsIEVSUk9SLCBFVkVOVF9UQVJHRVQsIENMSUNLIH0gZnJvbSAnLi9jb25zdGFudHMnO1xuZXhwb3J0IGZ1bmN0aW9uIGdldEluc3RydW1lbnRhdGlvbkZsYWdzKGluc3RydW1lbnQsIGRpc2FibGVkSW5zdHJ1bWVudGF0aW9ucykge1xuICB2YXIgX2ZsYWdzO1xuXG4gIHZhciBmbGFncyA9IChfZmxhZ3MgPSB7fSwgX2ZsYWdzW1hNTEhUVFBSRVFVRVNUXSA9IGZhbHNlLCBfZmxhZ3NbRkVUQ0hdID0gZmFsc2UsIF9mbGFnc1tISVNUT1JZXSA9IGZhbHNlLCBfZmxhZ3NbUEFHRV9MT0FEXSA9IGZhbHNlLCBfZmxhZ3NbRVJST1JdID0gZmFsc2UsIF9mbGFnc1tFVkVOVF9UQVJHRVRdID0gZmFsc2UsIF9mbGFnc1tDTElDS10gPSBmYWxzZSwgX2ZsYWdzKTtcblxuICBpZiAoIWluc3RydW1lbnQpIHtcbiAgICByZXR1cm4gZmxhZ3M7XG4gIH1cblxuICBPYmplY3Qua2V5cyhmbGFncykuZm9yRWFjaChmdW5jdGlvbiAoa2V5KSB7XG4gICAgaWYgKGRpc2FibGVkSW5zdHJ1bWVudGF0aW9ucy5pbmRleE9mKGtleSkgPT09IC0xKSB7XG4gICAgICBmbGFnc1trZXldID0gdHJ1ZTtcbiAgICB9XG4gIH0pO1xuICByZXR1cm4gZmxhZ3M7XG59IiwiaW1wb3J0IHsgbm9vcCB9IGZyb20gJy4vdXRpbHMnO1xuXG52YXIgTG9nZ2luZ1NlcnZpY2UgPSBmdW5jdGlvbiAoKSB7XG4gIGZ1bmN0aW9uIExvZ2dpbmdTZXJ2aWNlKHNwZWMpIHtcbiAgICBpZiAoc3BlYyA9PT0gdm9pZCAwKSB7XG4gICAgICBzcGVjID0ge307XG4gICAgfVxuXG4gICAgdGhpcy5sZXZlbHMgPSBbJ3RyYWNlJywgJ2RlYnVnJywgJ2luZm8nLCAnd2FybicsICdlcnJvciddO1xuICAgIHRoaXMubGV2ZWwgPSBzcGVjLmxldmVsIHx8ICd3YXJuJztcbiAgICB0aGlzLnByZWZpeCA9IHNwZWMucHJlZml4IHx8ICcnO1xuICAgIHRoaXMucmVzZXRMb2dNZXRob2RzKCk7XG4gIH1cblxuICB2YXIgX3Byb3RvID0gTG9nZ2luZ1NlcnZpY2UucHJvdG90eXBlO1xuXG4gIF9wcm90by5zaG91bGRMb2cgPSBmdW5jdGlvbiBzaG91bGRMb2cobGV2ZWwpIHtcbiAgICByZXR1cm4gdGhpcy5sZXZlbHMuaW5kZXhPZihsZXZlbCkgPj0gdGhpcy5sZXZlbHMuaW5kZXhPZih0aGlzLmxldmVsKTtcbiAgfTtcblxuICBfcHJvdG8uc2V0TGV2ZWwgPSBmdW5jdGlvbiBzZXRMZXZlbChsZXZlbCkge1xuICAgIGlmIChsZXZlbCA9PT0gdGhpcy5sZXZlbCkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIHRoaXMubGV2ZWwgPSBsZXZlbDtcbiAgICB0aGlzLnJlc2V0TG9nTWV0aG9kcygpO1xuICB9O1xuXG4gIF9wcm90by5yZXNldExvZ01ldGhvZHMgPSBmdW5jdGlvbiByZXNldExvZ01ldGhvZHMoKSB7XG4gICAgdmFyIF90aGlzID0gdGhpcztcblxuICAgIHRoaXMubGV2ZWxzLmZvckVhY2goZnVuY3Rpb24gKGxldmVsKSB7XG4gICAgICBfdGhpc1tsZXZlbF0gPSBfdGhpcy5zaG91bGRMb2cobGV2ZWwpID8gbG9nIDogbm9vcDtcblxuICAgICAgZnVuY3Rpb24gbG9nKCkge1xuICAgICAgICB2YXIgbm9ybWFsaXplZExldmVsID0gbGV2ZWw7XG5cbiAgICAgICAgaWYgKGxldmVsID09PSAndHJhY2UnIHx8IGxldmVsID09PSAnZGVidWcnKSB7XG4gICAgICAgICAgbm9ybWFsaXplZExldmVsID0gJ2luZm8nO1xuICAgICAgICB9XG5cbiAgICAgICAgdmFyIGFyZ3MgPSBhcmd1bWVudHM7XG4gICAgICAgIGFyZ3NbMF0gPSB0aGlzLnByZWZpeCArIGFyZ3NbMF07XG5cbiAgICAgICAgaWYgKGNvbnNvbGUpIHtcbiAgICAgICAgICB2YXIgcmVhbE1ldGhvZCA9IGNvbnNvbGVbbm9ybWFsaXplZExldmVsXSB8fCBjb25zb2xlLmxvZztcblxuICAgICAgICAgIGlmICh0eXBlb2YgcmVhbE1ldGhvZCA9PT0gJ2Z1bmN0aW9uJykge1xuICAgICAgICAgICAgcmVhbE1ldGhvZC5hcHBseShjb25zb2xlLCBhcmdzKTtcbiAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICAgIH1cbiAgICB9KTtcbiAgfTtcblxuICByZXR1cm4gTG9nZ2luZ1NlcnZpY2U7XG59KCk7XG5cbmV4cG9ydCBkZWZhdWx0IExvZ2dpbmdTZXJ2aWNlOyIsInZhciBOREpTT04gPSBmdW5jdGlvbiAoKSB7XG4gIGZ1bmN0aW9uIE5ESlNPTigpIHt9XG5cbiAgTkRKU09OLnN0cmluZ2lmeSA9IGZ1bmN0aW9uIHN0cmluZ2lmeShvYmplY3QpIHtcbiAgICByZXR1cm4gSlNPTi5zdHJpbmdpZnkob2JqZWN0KSArICdcXG4nO1xuICB9O1xuXG4gIHJldHVybiBOREpTT047XG59KCk7XG5cbmV4cG9ydCBkZWZhdWx0IE5ESlNPTjsiLCJpbXBvcnQgeyBVU0VSX0lOVEVSQUNUSU9OIH0gZnJvbSAnLi4vY29uc3RhbnRzJztcbmV4cG9ydCBmdW5jdGlvbiBvYnNlcnZlUGFnZUNsaWNrcyh0cmFuc2FjdGlvblNlcnZpY2UpIHtcbiAgdmFyIGNsaWNrSGFuZGxlciA9IGZ1bmN0aW9uIGNsaWNrSGFuZGxlcihldmVudCkge1xuICAgIGlmIChldmVudC50YXJnZXQgaW5zdGFuY2VvZiBFbGVtZW50KSB7XG4gICAgICBjcmVhdGVVc2VySW50ZXJhY3Rpb25UcmFuc2FjdGlvbih0cmFuc2FjdGlvblNlcnZpY2UsIGV2ZW50LnRhcmdldCk7XG4gICAgfVxuICB9O1xuXG4gIHZhciBldmVudE5hbWUgPSAnY2xpY2snO1xuICB2YXIgdXNlQ2FwdHVyZSA9IHRydWU7XG4gIHdpbmRvdy5hZGRFdmVudExpc3RlbmVyKGV2ZW50TmFtZSwgY2xpY2tIYW5kbGVyLCB1c2VDYXB0dXJlKTtcbiAgcmV0dXJuIGZ1bmN0aW9uICgpIHtcbiAgICB3aW5kb3cucmVtb3ZlRXZlbnRMaXN0ZW5lcihldmVudE5hbWUsIGNsaWNrSGFuZGxlciwgdXNlQ2FwdHVyZSk7XG4gIH07XG59XG5cbmZ1bmN0aW9uIGNyZWF0ZVVzZXJJbnRlcmFjdGlvblRyYW5zYWN0aW9uKHRyYW5zYWN0aW9uU2VydmljZSwgdGFyZ2V0KSB7XG4gIHZhciBfZ2V0VHJhbnNhY3Rpb25NZXRhZGEgPSBnZXRUcmFuc2FjdGlvbk1ldGFkYXRhKHRhcmdldCksXG4gICAgICB0cmFuc2FjdGlvbk5hbWUgPSBfZ2V0VHJhbnNhY3Rpb25NZXRhZGEudHJhbnNhY3Rpb25OYW1lLFxuICAgICAgY29udGV4dCA9IF9nZXRUcmFuc2FjdGlvbk1ldGFkYS5jb250ZXh0O1xuXG4gIHZhciB0ciA9IHRyYW5zYWN0aW9uU2VydmljZS5zdGFydFRyYW5zYWN0aW9uKFwiQ2xpY2sgLSBcIiArIHRyYW5zYWN0aW9uTmFtZSwgVVNFUl9JTlRFUkFDVElPTiwge1xuICAgIG1hbmFnZWQ6IHRydWUsXG4gICAgY2FuUmV1c2U6IHRydWUsXG4gICAgcmV1c2VUaHJlc2hvbGQ6IDMwMFxuICB9KTtcblxuICBpZiAodHIgJiYgY29udGV4dCkge1xuICAgIHRyLmFkZENvbnRleHQoY29udGV4dCk7XG4gIH1cbn1cblxuZnVuY3Rpb24gZ2V0VHJhbnNhY3Rpb25NZXRhZGF0YSh0YXJnZXQpIHtcbiAgdmFyIG1ldGFkYXRhID0ge1xuICAgIHRyYW5zYWN0aW9uTmFtZTogbnVsbCxcbiAgICBjb250ZXh0OiBudWxsXG4gIH07XG4gIHZhciB0YWdOYW1lID0gdGFyZ2V0LnRhZ05hbWUudG9Mb3dlckNhc2UoKTtcbiAgdmFyIHRyYW5zYWN0aW9uTmFtZSA9IHRhZ05hbWU7XG5cbiAgaWYgKCEhdGFyZ2V0LmRhdGFzZXQudHJhbnNhY3Rpb25OYW1lKSB7XG4gICAgdHJhbnNhY3Rpb25OYW1lID0gdGFyZ2V0LmRhdGFzZXQudHJhbnNhY3Rpb25OYW1lO1xuICB9IGVsc2Uge1xuICAgIHZhciBuYW1lID0gdGFyZ2V0LmdldEF0dHJpYnV0ZSgnbmFtZScpO1xuXG4gICAgaWYgKCEhbmFtZSkge1xuICAgICAgdHJhbnNhY3Rpb25OYW1lID0gdGFnTmFtZSArIFwiW1xcXCJcIiArIG5hbWUgKyBcIlxcXCJdXCI7XG4gICAgfVxuICB9XG5cbiAgbWV0YWRhdGEudHJhbnNhY3Rpb25OYW1lID0gdHJhbnNhY3Rpb25OYW1lO1xuICB2YXIgY2xhc3NlcyA9IHRhcmdldC5nZXRBdHRyaWJ1dGUoJ2NsYXNzJyk7XG5cbiAgaWYgKGNsYXNzZXMpIHtcbiAgICBtZXRhZGF0YS5jb250ZXh0ID0ge1xuICAgICAgY3VzdG9tOiB7XG4gICAgICAgIGNsYXNzZXM6IGNsYXNzZXNcbiAgICAgIH1cbiAgICB9O1xuICB9XG5cbiAgcmV0dXJuIG1ldGFkYXRhO1xufSIsImltcG9ydCB7IFFVRVVFX0FERF9UUkFOU0FDVElPTiwgUVVFVUVfRkxVU0ggfSBmcm9tICcuLi9jb25zdGFudHMnO1xuaW1wb3J0IHsgc3RhdGUgfSBmcm9tICcuLi8uLi9zdGF0ZSc7XG5pbXBvcnQgeyBub3cgfSBmcm9tICcuLi91dGlscyc7XG5leHBvcnQgZnVuY3Rpb24gb2JzZXJ2ZVBhZ2VWaXNpYmlsaXR5KGNvbmZpZ1NlcnZpY2UsIHRyYW5zYWN0aW9uU2VydmljZSkge1xuICBpZiAoZG9jdW1lbnQudmlzaWJpbGl0eVN0YXRlID09PSAnaGlkZGVuJykge1xuICAgIHN0YXRlLmxhc3RIaWRkZW5TdGFydCA9IDA7XG4gIH1cblxuICB2YXIgdmlzaWJpbGl0eUNoYW5nZUhhbmRsZXIgPSBmdW5jdGlvbiB2aXNpYmlsaXR5Q2hhbmdlSGFuZGxlcigpIHtcbiAgICBpZiAoZG9jdW1lbnQudmlzaWJpbGl0eVN0YXRlID09PSAnaGlkZGVuJykge1xuICAgICAgb25QYWdlSGlkZGVuKGNvbmZpZ1NlcnZpY2UsIHRyYW5zYWN0aW9uU2VydmljZSk7XG4gICAgfVxuICB9O1xuXG4gIHZhciBwYWdlSGlkZUhhbmRsZXIgPSBmdW5jdGlvbiBwYWdlSGlkZUhhbmRsZXIoKSB7XG4gICAgcmV0dXJuIG9uUGFnZUhpZGRlbihjb25maWdTZXJ2aWNlLCB0cmFuc2FjdGlvblNlcnZpY2UpO1xuICB9O1xuXG4gIHZhciB1c2VDYXB0dXJlID0gdHJ1ZTtcbiAgd2luZG93LmFkZEV2ZW50TGlzdGVuZXIoJ3Zpc2liaWxpdHljaGFuZ2UnLCB2aXNpYmlsaXR5Q2hhbmdlSGFuZGxlciwgdXNlQ2FwdHVyZSk7XG4gIHdpbmRvdy5hZGRFdmVudExpc3RlbmVyKCdwYWdlaGlkZScsIHBhZ2VIaWRlSGFuZGxlciwgdXNlQ2FwdHVyZSk7XG4gIHJldHVybiBmdW5jdGlvbiAoKSB7XG4gICAgd2luZG93LnJlbW92ZUV2ZW50TGlzdGVuZXIoJ3Zpc2liaWxpdHljaGFuZ2UnLCB2aXNpYmlsaXR5Q2hhbmdlSGFuZGxlciwgdXNlQ2FwdHVyZSk7XG4gICAgd2luZG93LnJlbW92ZUV2ZW50TGlzdGVuZXIoJ3BhZ2VoaWRlJywgcGFnZUhpZGVIYW5kbGVyLCB1c2VDYXB0dXJlKTtcbiAgfTtcbn1cblxuZnVuY3Rpb24gb25QYWdlSGlkZGVuKGNvbmZpZ1NlcnZpY2UsIHRyYW5zYWN0aW9uU2VydmljZSkge1xuICB2YXIgdHIgPSB0cmFuc2FjdGlvblNlcnZpY2UuZ2V0Q3VycmVudFRyYW5zYWN0aW9uKCk7XG5cbiAgaWYgKHRyKSB7XG4gICAgdmFyIHVub2JzZXJ2ZSA9IGNvbmZpZ1NlcnZpY2Uub2JzZXJ2ZUV2ZW50KFFVRVVFX0FERF9UUkFOU0FDVElPTiwgZnVuY3Rpb24gKCkge1xuICAgICAgY29uZmlnU2VydmljZS5kaXNwYXRjaEV2ZW50KFFVRVVFX0ZMVVNIKTtcbiAgICAgIHN0YXRlLmxhc3RIaWRkZW5TdGFydCA9IG5vdygpO1xuICAgICAgdW5vYnNlcnZlKCk7XG4gICAgfSk7XG4gICAgdHIuZW5kKCk7XG4gIH0gZWxzZSB7XG4gICAgY29uZmlnU2VydmljZS5kaXNwYXRjaEV2ZW50KFFVRVVFX0ZMVVNIKTtcbiAgICBzdGF0ZS5sYXN0SGlkZGVuU3RhcnQgPSBub3coKTtcbiAgfVxufSIsImltcG9ydCB7IFByb21pc2UgfSBmcm9tICcuLi9wb2x5ZmlsbHMnO1xuaW1wb3J0IHsgZ2xvYmFsU3RhdGUgfSBmcm9tICcuL3BhdGNoLXV0aWxzJztcbmltcG9ydCB7IFNDSEVEVUxFLCBJTlZPS0UsIEZFVENIIH0gZnJvbSAnLi4vY29uc3RhbnRzJztcbmltcG9ydCB7IHNjaGVkdWxlTWljcm9UYXNrIH0gZnJvbSAnLi4vdXRpbHMnO1xuaW1wb3J0IHsgaXNGZXRjaFN1cHBvcnRlZCB9IGZyb20gJy4uL2h0dHAvZmV0Y2gnO1xuZXhwb3J0IGZ1bmN0aW9uIHBhdGNoRmV0Y2goY2FsbGJhY2spIHtcbiAgaWYgKCFpc0ZldGNoU3VwcG9ydGVkKCkpIHtcbiAgICByZXR1cm47XG4gIH1cblxuICBmdW5jdGlvbiBzY2hlZHVsZVRhc2sodGFzaykge1xuICAgIHRhc2suc3RhdGUgPSBTQ0hFRFVMRTtcbiAgICBjYWxsYmFjayhTQ0hFRFVMRSwgdGFzayk7XG4gIH1cblxuICBmdW5jdGlvbiBpbnZva2VUYXNrKHRhc2spIHtcbiAgICB0YXNrLnN0YXRlID0gSU5WT0tFO1xuICAgIGNhbGxiYWNrKElOVk9LRSwgdGFzayk7XG4gIH1cblxuICBmdW5jdGlvbiBoYW5kbGVSZXNwb25zZUVycm9yKHRhc2ssIGVycm9yKSB7XG4gICAgdGFzay5kYXRhLmFib3J0ZWQgPSBpc0Fib3J0RXJyb3IoZXJyb3IpO1xuICAgIHRhc2suZGF0YS5lcnJvciA9IGVycm9yO1xuICAgIGludm9rZVRhc2sodGFzayk7XG4gIH1cblxuICBmdW5jdGlvbiByZWFkU3RyZWFtKHN0cmVhbSwgdGFzaykge1xuICAgIHZhciByZWFkZXIgPSBzdHJlYW0uZ2V0UmVhZGVyKCk7XG5cbiAgICB2YXIgcmVhZCA9IGZ1bmN0aW9uIHJlYWQoKSB7XG4gICAgICByZWFkZXIucmVhZCgpLnRoZW4oZnVuY3Rpb24gKF9yZWYpIHtcbiAgICAgICAgdmFyIGRvbmUgPSBfcmVmLmRvbmU7XG5cbiAgICAgICAgaWYgKGRvbmUpIHtcbiAgICAgICAgICBpbnZva2VUYXNrKHRhc2spO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgIHJlYWQoKTtcbiAgICAgICAgfVxuICAgICAgfSwgZnVuY3Rpb24gKGVycm9yKSB7XG4gICAgICAgIGhhbmRsZVJlc3BvbnNlRXJyb3IodGFzaywgZXJyb3IpO1xuICAgICAgfSk7XG4gICAgfTtcblxuICAgIHJlYWQoKTtcbiAgfVxuXG4gIHZhciBuYXRpdmVGZXRjaCA9IHdpbmRvdy5mZXRjaDtcblxuICB3aW5kb3cuZmV0Y2ggPSBmdW5jdGlvbiAoaW5wdXQsIGluaXQpIHtcbiAgICB2YXIgZmV0Y2hTZWxmID0gdGhpcztcbiAgICB2YXIgYXJncyA9IGFyZ3VtZW50cztcbiAgICB2YXIgcmVxdWVzdCwgdXJsO1xuXG4gICAgaWYgKHR5cGVvZiBpbnB1dCA9PT0gJ3N0cmluZycpIHtcbiAgICAgIHJlcXVlc3QgPSBuZXcgUmVxdWVzdChpbnB1dCwgaW5pdCk7XG4gICAgICB1cmwgPSBpbnB1dDtcbiAgICB9IGVsc2UgaWYgKGlucHV0KSB7XG4gICAgICByZXF1ZXN0ID0gaW5wdXQ7XG4gICAgICB1cmwgPSByZXF1ZXN0LnVybDtcbiAgICB9IGVsc2Uge1xuICAgICAgcmV0dXJuIG5hdGl2ZUZldGNoLmFwcGx5KGZldGNoU2VsZiwgYXJncyk7XG4gICAgfVxuXG4gICAgdmFyIHRhc2sgPSB7XG4gICAgICBzb3VyY2U6IEZFVENILFxuICAgICAgc3RhdGU6ICcnLFxuICAgICAgdHlwZTogJ21hY3JvVGFzaycsXG4gICAgICBkYXRhOiB7XG4gICAgICAgIHRhcmdldDogcmVxdWVzdCxcbiAgICAgICAgbWV0aG9kOiByZXF1ZXN0Lm1ldGhvZCxcbiAgICAgICAgdXJsOiB1cmwsXG4gICAgICAgIGFib3J0ZWQ6IGZhbHNlXG4gICAgICB9XG4gICAgfTtcbiAgICByZXR1cm4gbmV3IFByb21pc2UoZnVuY3Rpb24gKHJlc29sdmUsIHJlamVjdCkge1xuICAgICAgZ2xvYmFsU3RhdGUuZmV0Y2hJblByb2dyZXNzID0gdHJ1ZTtcbiAgICAgIHNjaGVkdWxlVGFzayh0YXNrKTtcbiAgICAgIHZhciBwcm9taXNlO1xuXG4gICAgICB0cnkge1xuICAgICAgICBwcm9taXNlID0gbmF0aXZlRmV0Y2guYXBwbHkoZmV0Y2hTZWxmLCBbcmVxdWVzdF0pO1xuICAgICAgfSBjYXRjaCAoZXJyb3IpIHtcbiAgICAgICAgcmVqZWN0KGVycm9yKTtcbiAgICAgICAgdGFzay5kYXRhLmVycm9yID0gZXJyb3I7XG4gICAgICAgIGludm9rZVRhc2sodGFzayk7XG4gICAgICAgIGdsb2JhbFN0YXRlLmZldGNoSW5Qcm9ncmVzcyA9IGZhbHNlO1xuICAgICAgICByZXR1cm47XG4gICAgICB9XG5cbiAgICAgIHByb21pc2UudGhlbihmdW5jdGlvbiAocmVzcG9uc2UpIHtcbiAgICAgICAgdmFyIGNsb25lZFJlc3BvbnNlID0gcmVzcG9uc2UuY2xvbmUgPyByZXNwb25zZS5jbG9uZSgpIDoge307XG4gICAgICAgIHJlc29sdmUocmVzcG9uc2UpO1xuICAgICAgICBzY2hlZHVsZU1pY3JvVGFzayhmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgdGFzay5kYXRhLnJlc3BvbnNlID0gcmVzcG9uc2U7XG4gICAgICAgICAgdmFyIGJvZHkgPSBjbG9uZWRSZXNwb25zZS5ib2R5O1xuXG4gICAgICAgICAgaWYgKGJvZHkpIHtcbiAgICAgICAgICAgIHJlYWRTdHJlYW0oYm9keSwgdGFzayk7XG4gICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgIGludm9rZVRhc2sodGFzayk7XG4gICAgICAgICAgfVxuICAgICAgICB9KTtcbiAgICAgIH0sIGZ1bmN0aW9uIChlcnJvcikge1xuICAgICAgICByZWplY3QoZXJyb3IpO1xuICAgICAgICBzY2hlZHVsZU1pY3JvVGFzayhmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgaGFuZGxlUmVzcG9uc2VFcnJvcih0YXNrLCBlcnJvcik7XG4gICAgICAgIH0pO1xuICAgICAgfSk7XG4gICAgICBnbG9iYWxTdGF0ZS5mZXRjaEluUHJvZ3Jlc3MgPSBmYWxzZTtcbiAgICB9KTtcbiAgfTtcbn1cblxuZnVuY3Rpb24gaXNBYm9ydEVycm9yKGVycm9yKSB7XG4gIHJldHVybiBlcnJvciAmJiBlcnJvci5uYW1lID09PSAnQWJvcnRFcnJvcic7XG59IiwiaW1wb3J0IHsgSU5WT0tFLCBISVNUT1JZIH0gZnJvbSAnLi4vY29uc3RhbnRzJztcbmV4cG9ydCBmdW5jdGlvbiBwYXRjaEhpc3RvcnkoY2FsbGJhY2spIHtcbiAgaWYgKCF3aW5kb3cuaGlzdG9yeSkge1xuICAgIHJldHVybjtcbiAgfVxuXG4gIHZhciBuYXRpdmVQdXNoU3RhdGUgPSBoaXN0b3J5LnB1c2hTdGF0ZTtcblxuICBpZiAodHlwZW9mIG5hdGl2ZVB1c2hTdGF0ZSA9PT0gJ2Z1bmN0aW9uJykge1xuICAgIGhpc3RvcnkucHVzaFN0YXRlID0gZnVuY3Rpb24gKHN0YXRlLCB0aXRsZSwgdXJsKSB7XG4gICAgICB2YXIgdGFzayA9IHtcbiAgICAgICAgc291cmNlOiBISVNUT1JZLFxuICAgICAgICBkYXRhOiB7XG4gICAgICAgICAgc3RhdGU6IHN0YXRlLFxuICAgICAgICAgIHRpdGxlOiB0aXRsZSxcbiAgICAgICAgICB1cmw6IHVybFxuICAgICAgICB9XG4gICAgICB9O1xuICAgICAgY2FsbGJhY2soSU5WT0tFLCB0YXNrKTtcbiAgICAgIG5hdGl2ZVB1c2hTdGF0ZS5hcHBseSh0aGlzLCBhcmd1bWVudHMpO1xuICAgIH07XG4gIH1cbn0iLCJpbXBvcnQgeyBwYXRjaFhNTEh0dHBSZXF1ZXN0IH0gZnJvbSAnLi94aHItcGF0Y2gnO1xuaW1wb3J0IHsgcGF0Y2hGZXRjaCB9IGZyb20gJy4vZmV0Y2gtcGF0Y2gnO1xuaW1wb3J0IHsgcGF0Y2hIaXN0b3J5IH0gZnJvbSAnLi9oaXN0b3J5LXBhdGNoJztcbmltcG9ydCBFdmVudEhhbmRsZXIgZnJvbSAnLi4vZXZlbnQtaGFuZGxlcic7XG5pbXBvcnQgeyBISVNUT1JZLCBGRVRDSCwgWE1MSFRUUFJFUVVFU1QgfSBmcm9tICcuLi9jb25zdGFudHMnO1xudmFyIHBhdGNoRXZlbnRIYW5kbGVyID0gbmV3IEV2ZW50SGFuZGxlcigpO1xudmFyIGFscmVhZHlQYXRjaGVkID0gZmFsc2U7XG5cbmZ1bmN0aW9uIHBhdGNoQWxsKCkge1xuICBpZiAoIWFscmVhZHlQYXRjaGVkKSB7XG4gICAgYWxyZWFkeVBhdGNoZWQgPSB0cnVlO1xuICAgIHBhdGNoWE1MSHR0cFJlcXVlc3QoZnVuY3Rpb24gKGV2ZW50LCB0YXNrKSB7XG4gICAgICBwYXRjaEV2ZW50SGFuZGxlci5zZW5kKFhNTEhUVFBSRVFVRVNULCBbZXZlbnQsIHRhc2tdKTtcbiAgICB9KTtcbiAgICBwYXRjaEZldGNoKGZ1bmN0aW9uIChldmVudCwgdGFzaykge1xuICAgICAgcGF0Y2hFdmVudEhhbmRsZXIuc2VuZChGRVRDSCwgW2V2ZW50LCB0YXNrXSk7XG4gICAgfSk7XG4gICAgcGF0Y2hIaXN0b3J5KGZ1bmN0aW9uIChldmVudCwgdGFzaykge1xuICAgICAgcGF0Y2hFdmVudEhhbmRsZXIuc2VuZChISVNUT1JZLCBbZXZlbnQsIHRhc2tdKTtcbiAgICB9KTtcbiAgfVxuXG4gIHJldHVybiBwYXRjaEV2ZW50SGFuZGxlcjtcbn1cblxuZXhwb3J0IHsgcGF0Y2hBbGwsIHBhdGNoRXZlbnRIYW5kbGVyIH07IiwiZXhwb3J0IHZhciBnbG9iYWxTdGF0ZSA9IHtcbiAgZmV0Y2hJblByb2dyZXNzOiBmYWxzZVxufTtcbmV4cG9ydCBmdW5jdGlvbiBhcG1TeW1ib2wobmFtZSkge1xuICByZXR1cm4gJ19fYXBtX3N5bWJvbF9fJyArIG5hbWU7XG59XG5cbmZ1bmN0aW9uIGlzUHJvcGVydHlXcml0YWJsZShwcm9wZXJ0eURlc2MpIHtcbiAgaWYgKCFwcm9wZXJ0eURlc2MpIHtcbiAgICByZXR1cm4gdHJ1ZTtcbiAgfVxuXG4gIGlmIChwcm9wZXJ0eURlc2Mud3JpdGFibGUgPT09IGZhbHNlKSB7XG4gICAgcmV0dXJuIGZhbHNlO1xuICB9XG5cbiAgcmV0dXJuICEodHlwZW9mIHByb3BlcnR5RGVzYy5nZXQgPT09ICdmdW5jdGlvbicgJiYgdHlwZW9mIHByb3BlcnR5RGVzYy5zZXQgPT09ICd1bmRlZmluZWQnKTtcbn1cblxuZnVuY3Rpb24gYXR0YWNoT3JpZ2luVG9QYXRjaGVkKHBhdGNoZWQsIG9yaWdpbmFsKSB7XG4gIHBhdGNoZWRbYXBtU3ltYm9sKCdPcmlnaW5hbERlbGVnYXRlJyldID0gb3JpZ2luYWw7XG59XG5cbmV4cG9ydCBmdW5jdGlvbiBwYXRjaE1ldGhvZCh0YXJnZXQsIG5hbWUsIHBhdGNoRm4pIHtcbiAgdmFyIHByb3RvID0gdGFyZ2V0O1xuXG4gIHdoaWxlIChwcm90byAmJiAhcHJvdG8uaGFzT3duUHJvcGVydHkobmFtZSkpIHtcbiAgICBwcm90byA9IE9iamVjdC5nZXRQcm90b3R5cGVPZihwcm90byk7XG4gIH1cblxuICBpZiAoIXByb3RvICYmIHRhcmdldFtuYW1lXSkge1xuICAgIHByb3RvID0gdGFyZ2V0O1xuICB9XG5cbiAgdmFyIGRlbGVnYXRlTmFtZSA9IGFwbVN5bWJvbChuYW1lKTtcbiAgdmFyIGRlbGVnYXRlO1xuXG4gIGlmIChwcm90byAmJiAhKGRlbGVnYXRlID0gcHJvdG9bZGVsZWdhdGVOYW1lXSkpIHtcbiAgICBkZWxlZ2F0ZSA9IHByb3RvW2RlbGVnYXRlTmFtZV0gPSBwcm90b1tuYW1lXTtcbiAgICB2YXIgZGVzYyA9IHByb3RvICYmIE9iamVjdC5nZXRPd25Qcm9wZXJ0eURlc2NyaXB0b3IocHJvdG8sIG5hbWUpO1xuXG4gICAgaWYgKGlzUHJvcGVydHlXcml0YWJsZShkZXNjKSkge1xuICAgICAgdmFyIHBhdGNoRGVsZWdhdGUgPSBwYXRjaEZuKGRlbGVnYXRlLCBkZWxlZ2F0ZU5hbWUsIG5hbWUpO1xuXG4gICAgICBwcm90b1tuYW1lXSA9IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgcmV0dXJuIHBhdGNoRGVsZWdhdGUodGhpcywgYXJndW1lbnRzKTtcbiAgICAgIH07XG5cbiAgICAgIGF0dGFjaE9yaWdpblRvUGF0Y2hlZChwcm90b1tuYW1lXSwgZGVsZWdhdGUpO1xuICAgIH1cbiAgfVxuXG4gIHJldHVybiBkZWxlZ2F0ZTtcbn1cbmV4cG9ydCB2YXIgWEhSX0lHTk9SRSA9IGFwbVN5bWJvbCgneGhySWdub3JlJyk7XG5leHBvcnQgdmFyIFhIUl9TWU5DID0gYXBtU3ltYm9sKCd4aHJTeW5jJyk7XG5leHBvcnQgdmFyIFhIUl9VUkwgPSBhcG1TeW1ib2woJ3hoclVSTCcpO1xuZXhwb3J0IHZhciBYSFJfTUVUSE9EID0gYXBtU3ltYm9sKCd4aHJNZXRob2QnKTsiLCJpbXBvcnQgeyBwYXRjaE1ldGhvZCwgWEhSX1NZTkMsIFhIUl9VUkwsIFhIUl9NRVRIT0QsIFhIUl9JR05PUkUgfSBmcm9tICcuL3BhdGNoLXV0aWxzJztcbmltcG9ydCB7IFNDSEVEVUxFLCBJTlZPS0UsIFhNTEhUVFBSRVFVRVNULCBBRERfRVZFTlRfTElTVEVORVJfU1RSIH0gZnJvbSAnLi4vY29uc3RhbnRzJztcbmV4cG9ydCBmdW5jdGlvbiBwYXRjaFhNTEh0dHBSZXF1ZXN0KGNhbGxiYWNrKSB7XG4gIHZhciBYTUxIdHRwUmVxdWVzdFByb3RvdHlwZSA9IFhNTEh0dHBSZXF1ZXN0LnByb3RvdHlwZTtcblxuICBpZiAoIVhNTEh0dHBSZXF1ZXN0UHJvdG90eXBlIHx8ICFYTUxIdHRwUmVxdWVzdFByb3RvdHlwZVtBRERfRVZFTlRfTElTVEVORVJfU1RSXSkge1xuICAgIHJldHVybjtcbiAgfVxuXG4gIHZhciBSRUFEWV9TVEFURV9DSEFOR0UgPSAncmVhZHlzdGF0ZWNoYW5nZSc7XG4gIHZhciBMT0FEID0gJ2xvYWQnO1xuICB2YXIgRVJST1IgPSAnZXJyb3InO1xuICB2YXIgVElNRU9VVCA9ICd0aW1lb3V0JztcbiAgdmFyIEFCT1JUID0gJ2Fib3J0JztcblxuICBmdW5jdGlvbiBpbnZva2VUYXNrKHRhc2ssIHN0YXR1cykge1xuICAgIGlmICh0YXNrLnN0YXRlICE9PSBJTlZPS0UpIHtcbiAgICAgIHRhc2suc3RhdGUgPSBJTlZPS0U7XG4gICAgICB0YXNrLmRhdGEuc3RhdHVzID0gc3RhdHVzO1xuICAgICAgY2FsbGJhY2soSU5WT0tFLCB0YXNrKTtcbiAgICB9XG4gIH1cblxuICBmdW5jdGlvbiBzY2hlZHVsZVRhc2sodGFzaykge1xuICAgIGlmICh0YXNrLnN0YXRlID09PSBTQ0hFRFVMRSkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIHRhc2suc3RhdGUgPSBTQ0hFRFVMRTtcbiAgICBjYWxsYmFjayhTQ0hFRFVMRSwgdGFzayk7XG4gICAgdmFyIHRhcmdldCA9IHRhc2suZGF0YS50YXJnZXQ7XG5cbiAgICBmdW5jdGlvbiBhZGRMaXN0ZW5lcihuYW1lKSB7XG4gICAgICB0YXJnZXRbQUREX0VWRU5UX0xJU1RFTkVSX1NUUl0obmFtZSwgZnVuY3Rpb24gKF9yZWYpIHtcbiAgICAgICAgdmFyIHR5cGUgPSBfcmVmLnR5cGU7XG5cbiAgICAgICAgaWYgKHR5cGUgPT09IFJFQURZX1NUQVRFX0NIQU5HRSkge1xuICAgICAgICAgIGlmICh0YXJnZXQucmVhZHlTdGF0ZSA9PT0gNCAmJiB0YXJnZXQuc3RhdHVzICE9PSAwKSB7XG4gICAgICAgICAgICBpbnZva2VUYXNrKHRhc2ssICdzdWNjZXNzJyk7XG4gICAgICAgICAgfVxuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgIHZhciBzdGF0dXMgPSB0eXBlID09PSBMT0FEID8gJ3N1Y2Nlc3MnIDogdHlwZTtcbiAgICAgICAgICBpbnZva2VUYXNrKHRhc2ssIHN0YXR1cyk7XG4gICAgICAgIH1cbiAgICAgIH0pO1xuICAgIH1cblxuICAgIGFkZExpc3RlbmVyKFJFQURZX1NUQVRFX0NIQU5HRSk7XG4gICAgYWRkTGlzdGVuZXIoTE9BRCk7XG4gICAgYWRkTGlzdGVuZXIoVElNRU9VVCk7XG4gICAgYWRkTGlzdGVuZXIoRVJST1IpO1xuICAgIGFkZExpc3RlbmVyKEFCT1JUKTtcbiAgfVxuXG4gIHZhciBvcGVuTmF0aXZlID0gcGF0Y2hNZXRob2QoWE1MSHR0cFJlcXVlc3RQcm90b3R5cGUsICdvcGVuJywgZnVuY3Rpb24gKCkge1xuICAgIHJldHVybiBmdW5jdGlvbiAoc2VsZiwgYXJncykge1xuICAgICAgaWYgKCFzZWxmW1hIUl9JR05PUkVdKSB7XG4gICAgICAgIHNlbGZbWEhSX01FVEhPRF0gPSBhcmdzWzBdO1xuICAgICAgICBzZWxmW1hIUl9VUkxdID0gYXJnc1sxXTtcbiAgICAgICAgc2VsZltYSFJfU1lOQ10gPSBhcmdzWzJdID09PSBmYWxzZTtcbiAgICAgIH1cblxuICAgICAgcmV0dXJuIG9wZW5OYXRpdmUuYXBwbHkoc2VsZiwgYXJncyk7XG4gICAgfTtcbiAgfSk7XG4gIHZhciBzZW5kTmF0aXZlID0gcGF0Y2hNZXRob2QoWE1MSHR0cFJlcXVlc3RQcm90b3R5cGUsICdzZW5kJywgZnVuY3Rpb24gKCkge1xuICAgIHJldHVybiBmdW5jdGlvbiAoc2VsZiwgYXJncykge1xuICAgICAgaWYgKHNlbGZbWEhSX0lHTk9SRV0pIHtcbiAgICAgICAgcmV0dXJuIHNlbmROYXRpdmUuYXBwbHkoc2VsZiwgYXJncyk7XG4gICAgICB9XG5cbiAgICAgIHZhciB0YXNrID0ge1xuICAgICAgICBzb3VyY2U6IFhNTEhUVFBSRVFVRVNULFxuICAgICAgICBzdGF0ZTogJycsXG4gICAgICAgIHR5cGU6ICdtYWNyb1Rhc2snLFxuICAgICAgICBkYXRhOiB7XG4gICAgICAgICAgdGFyZ2V0OiBzZWxmLFxuICAgICAgICAgIG1ldGhvZDogc2VsZltYSFJfTUVUSE9EXSxcbiAgICAgICAgICBzeW5jOiBzZWxmW1hIUl9TWU5DXSxcbiAgICAgICAgICB1cmw6IHNlbGZbWEhSX1VSTF0sXG4gICAgICAgICAgc3RhdHVzOiAnJ1xuICAgICAgICB9XG4gICAgICB9O1xuXG4gICAgICB0cnkge1xuICAgICAgICBzY2hlZHVsZVRhc2sodGFzayk7XG4gICAgICAgIHJldHVybiBzZW5kTmF0aXZlLmFwcGx5KHNlbGYsIGFyZ3MpO1xuICAgICAgfSBjYXRjaCAoZSkge1xuICAgICAgICBpbnZva2VUYXNrKHRhc2ssIEVSUk9SKTtcbiAgICAgICAgdGhyb3cgZTtcbiAgICAgIH1cbiAgICB9O1xuICB9KTtcbn0iLCJpbXBvcnQgUHJvbWlzZVBvbGx5ZmlsbCBmcm9tICdwcm9taXNlLXBvbHlmaWxsJztcbmltcG9ydCB7IGlzQnJvd3NlciB9IGZyb20gJy4vdXRpbHMnO1xudmFyIGxvY2FsID0ge307XG5cbmlmIChpc0Jyb3dzZXIpIHtcbiAgbG9jYWwgPSB3aW5kb3c7XG59IGVsc2UgaWYgKHR5cGVvZiBzZWxmICE9PSAndW5kZWZpbmVkJykge1xuICBsb2NhbCA9IHNlbGY7XG59XG5cbnZhciBQcm9taXNlID0gJ1Byb21pc2UnIGluIGxvY2FsID8gbG9jYWwuUHJvbWlzZSA6IFByb21pc2VQb2xseWZpbGw7XG5leHBvcnQgeyBQcm9taXNlIH07IiwidmFyIFF1ZXVlID0gZnVuY3Rpb24gKCkge1xuICBmdW5jdGlvbiBRdWV1ZShvbkZsdXNoLCBvcHRzKSB7XG4gICAgaWYgKG9wdHMgPT09IHZvaWQgMCkge1xuICAgICAgb3B0cyA9IHt9O1xuICAgIH1cblxuICAgIHRoaXMub25GbHVzaCA9IG9uRmx1c2g7XG4gICAgdGhpcy5pdGVtcyA9IFtdO1xuICAgIHRoaXMucXVldWVMaW1pdCA9IG9wdHMucXVldWVMaW1pdCB8fCAtMTtcbiAgICB0aGlzLmZsdXNoSW50ZXJ2YWwgPSBvcHRzLmZsdXNoSW50ZXJ2YWwgfHwgMDtcbiAgICB0aGlzLnRpbWVvdXRJZCA9IHVuZGVmaW5lZDtcbiAgfVxuXG4gIHZhciBfcHJvdG8gPSBRdWV1ZS5wcm90b3R5cGU7XG5cbiAgX3Byb3RvLl9zZXRUaW1lciA9IGZ1bmN0aW9uIF9zZXRUaW1lcigpIHtcbiAgICB2YXIgX3RoaXMgPSB0aGlzO1xuXG4gICAgdGhpcy50aW1lb3V0SWQgPSBzZXRUaW1lb3V0KGZ1bmN0aW9uICgpIHtcbiAgICAgIHJldHVybiBfdGhpcy5mbHVzaCgpO1xuICAgIH0sIHRoaXMuZmx1c2hJbnRlcnZhbCk7XG4gIH07XG5cbiAgX3Byb3RvLl9jbGVhciA9IGZ1bmN0aW9uIF9jbGVhcigpIHtcbiAgICBpZiAodHlwZW9mIHRoaXMudGltZW91dElkICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgY2xlYXJUaW1lb3V0KHRoaXMudGltZW91dElkKTtcbiAgICAgIHRoaXMudGltZW91dElkID0gdW5kZWZpbmVkO1xuICAgIH1cblxuICAgIHRoaXMuaXRlbXMgPSBbXTtcbiAgfTtcblxuICBfcHJvdG8uZmx1c2ggPSBmdW5jdGlvbiBmbHVzaCgpIHtcbiAgICB0aGlzLm9uRmx1c2godGhpcy5pdGVtcyk7XG5cbiAgICB0aGlzLl9jbGVhcigpO1xuICB9O1xuXG4gIF9wcm90by5hZGQgPSBmdW5jdGlvbiBhZGQoaXRlbSkge1xuICAgIHRoaXMuaXRlbXMucHVzaChpdGVtKTtcblxuICAgIGlmICh0aGlzLnF1ZXVlTGltaXQgIT09IC0xICYmIHRoaXMuaXRlbXMubGVuZ3RoID49IHRoaXMucXVldWVMaW1pdCkge1xuICAgICAgdGhpcy5mbHVzaCgpO1xuICAgIH0gZWxzZSB7XG4gICAgICBpZiAodHlwZW9mIHRoaXMudGltZW91dElkID09PSAndW5kZWZpbmVkJykge1xuICAgICAgICB0aGlzLl9zZXRUaW1lcigpO1xuICAgICAgfVxuICAgIH1cbiAgfTtcblxuICByZXR1cm4gUXVldWU7XG59KCk7XG5cbmV4cG9ydCBkZWZhdWx0IFF1ZXVlOyIsInZhciBfc2VydmljZUNyZWF0b3JzO1xuXG5pbXBvcnQgQXBtU2VydmVyIGZyb20gJy4vYXBtLXNlcnZlcic7XG5pbXBvcnQgQ29uZmlnU2VydmljZSBmcm9tICcuL2NvbmZpZy1zZXJ2aWNlJztcbmltcG9ydCBMb2dnaW5nU2VydmljZSBmcm9tICcuL2xvZ2dpbmctc2VydmljZSc7XG5pbXBvcnQgeyBDT05GSUdfQ0hBTkdFLCBDT05GSUdfU0VSVklDRSwgTE9HR0lOR19TRVJWSUNFLCBBUE1fU0VSVkVSIH0gZnJvbSAnLi9jb25zdGFudHMnO1xuaW1wb3J0IHsgX19ERVZfXyB9IGZyb20gJy4uL3N0YXRlJztcbnZhciBzZXJ2aWNlQ3JlYXRvcnMgPSAoX3NlcnZpY2VDcmVhdG9ycyA9IHt9LCBfc2VydmljZUNyZWF0b3JzW0NPTkZJR19TRVJWSUNFXSA9IGZ1bmN0aW9uICgpIHtcbiAgcmV0dXJuIG5ldyBDb25maWdTZXJ2aWNlKCk7XG59LCBfc2VydmljZUNyZWF0b3JzW0xPR0dJTkdfU0VSVklDRV0gPSBmdW5jdGlvbiAoKSB7XG4gIHJldHVybiBuZXcgTG9nZ2luZ1NlcnZpY2Uoe1xuICAgIHByZWZpeDogJ1tFbGFzdGljIEFQTV0gJ1xuICB9KTtcbn0sIF9zZXJ2aWNlQ3JlYXRvcnNbQVBNX1NFUlZFUl0gPSBmdW5jdGlvbiAoZmFjdG9yeSkge1xuICB2YXIgX2ZhY3RvcnkkZ2V0U2VydmljZSA9IGZhY3RvcnkuZ2V0U2VydmljZShbQ09ORklHX1NFUlZJQ0UsIExPR0dJTkdfU0VSVklDRV0pLFxuICAgICAgY29uZmlnU2VydmljZSA9IF9mYWN0b3J5JGdldFNlcnZpY2VbMF0sXG4gICAgICBsb2dnaW5nU2VydmljZSA9IF9mYWN0b3J5JGdldFNlcnZpY2VbMV07XG5cbiAgcmV0dXJuIG5ldyBBcG1TZXJ2ZXIoY29uZmlnU2VydmljZSwgbG9nZ2luZ1NlcnZpY2UpO1xufSwgX3NlcnZpY2VDcmVhdG9ycyk7XG5cbnZhciBTZXJ2aWNlRmFjdG9yeSA9IGZ1bmN0aW9uICgpIHtcbiAgZnVuY3Rpb24gU2VydmljZUZhY3RvcnkoKSB7XG4gICAgdGhpcy5pbnN0YW5jZXMgPSB7fTtcbiAgICB0aGlzLmluaXRpYWxpemVkID0gZmFsc2U7XG4gIH1cblxuICB2YXIgX3Byb3RvID0gU2VydmljZUZhY3RvcnkucHJvdG90eXBlO1xuXG4gIF9wcm90by5pbml0ID0gZnVuY3Rpb24gaW5pdCgpIHtcbiAgICBpZiAodGhpcy5pbml0aWFsaXplZCkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIHRoaXMuaW5pdGlhbGl6ZWQgPSB0cnVlO1xuICAgIHZhciBjb25maWdTZXJ2aWNlID0gdGhpcy5nZXRTZXJ2aWNlKENPTkZJR19TRVJWSUNFKTtcbiAgICBjb25maWdTZXJ2aWNlLmluaXQoKTtcblxuICAgIHZhciBfdGhpcyRnZXRTZXJ2aWNlID0gdGhpcy5nZXRTZXJ2aWNlKFtMT0dHSU5HX1NFUlZJQ0UsIEFQTV9TRVJWRVJdKSxcbiAgICAgICAgbG9nZ2luZ1NlcnZpY2UgPSBfdGhpcyRnZXRTZXJ2aWNlWzBdLFxuICAgICAgICBhcG1TZXJ2ZXIgPSBfdGhpcyRnZXRTZXJ2aWNlWzFdO1xuXG4gICAgY29uZmlnU2VydmljZS5ldmVudHMub2JzZXJ2ZShDT05GSUdfQ0hBTkdFLCBmdW5jdGlvbiAoKSB7XG4gICAgICB2YXIgbG9nTGV2ZWwgPSBjb25maWdTZXJ2aWNlLmdldCgnbG9nTGV2ZWwnKTtcbiAgICAgIGxvZ2dpbmdTZXJ2aWNlLnNldExldmVsKGxvZ0xldmVsKTtcbiAgICB9KTtcbiAgICBhcG1TZXJ2ZXIuaW5pdCgpO1xuICB9O1xuXG4gIF9wcm90by5nZXRTZXJ2aWNlID0gZnVuY3Rpb24gZ2V0U2VydmljZShuYW1lKSB7XG4gICAgdmFyIF90aGlzID0gdGhpcztcblxuICAgIGlmICh0eXBlb2YgbmFtZSA9PT0gJ3N0cmluZycpIHtcbiAgICAgIGlmICghdGhpcy5pbnN0YW5jZXNbbmFtZV0pIHtcbiAgICAgICAgaWYgKHR5cGVvZiBzZXJ2aWNlQ3JlYXRvcnNbbmFtZV0gPT09ICdmdW5jdGlvbicpIHtcbiAgICAgICAgICB0aGlzLmluc3RhbmNlc1tuYW1lXSA9IHNlcnZpY2VDcmVhdG9yc1tuYW1lXSh0aGlzKTtcbiAgICAgICAgfSBlbHNlIGlmIChfX0RFVl9fKSB7XG4gICAgICAgICAgY29uc29sZS5sb2coJ0Nhbm5vdCBnZXQgc2VydmljZSwgTm8gY3JlYXRvciBmb3I6ICcgKyBuYW1lKTtcbiAgICAgICAgfVxuICAgICAgfVxuXG4gICAgICByZXR1cm4gdGhpcy5pbnN0YW5jZXNbbmFtZV07XG4gICAgfSBlbHNlIGlmIChBcnJheS5pc0FycmF5KG5hbWUpKSB7XG4gICAgICByZXR1cm4gbmFtZS5tYXAoZnVuY3Rpb24gKG4pIHtcbiAgICAgICAgcmV0dXJuIF90aGlzLmdldFNlcnZpY2Uobik7XG4gICAgICB9KTtcbiAgICB9XG4gIH07XG5cbiAgcmV0dXJuIFNlcnZpY2VGYWN0b3J5O1xufSgpO1xuXG5leHBvcnQgeyBzZXJ2aWNlQ3JlYXRvcnMsIFNlcnZpY2VGYWN0b3J5IH07IiwiZXhwb3J0IGRlZmF1bHQgZnVuY3Rpb24gdGhyb3R0bGUoZm4sIG9uVGhyb3R0bGUsIG9wdHMpIHtcbiAgdmFyIGNvbnRleHQgPSB0aGlzO1xuICB2YXIgbGltaXQgPSBvcHRzLmxpbWl0O1xuICB2YXIgaW50ZXJ2YWwgPSBvcHRzLmludGVydmFsO1xuICB2YXIgY291bnRlciA9IDA7XG4gIHZhciB0aW1lb3V0SWQ7XG4gIHJldHVybiBmdW5jdGlvbiAoKSB7XG4gICAgY291bnRlcisrO1xuXG4gICAgaWYgKHR5cGVvZiB0aW1lb3V0SWQgPT09ICd1bmRlZmluZWQnKSB7XG4gICAgICB0aW1lb3V0SWQgPSBzZXRUaW1lb3V0KGZ1bmN0aW9uICgpIHtcbiAgICAgICAgY291bnRlciA9IDA7XG4gICAgICAgIHRpbWVvdXRJZCA9IHVuZGVmaW5lZDtcbiAgICAgIH0sIGludGVydmFsKTtcbiAgICB9XG5cbiAgICBpZiAoY291bnRlciA+IGxpbWl0ICYmIHR5cGVvZiBvblRocm90dGxlID09PSAnZnVuY3Rpb24nKSB7XG4gICAgICByZXR1cm4gb25UaHJvdHRsZS5hcHBseShjb250ZXh0LCBhcmd1bWVudHMpO1xuICAgIH0gZWxzZSB7XG4gICAgICByZXR1cm4gZm4uYXBwbHkoY29udGV4dCwgYXJndW1lbnRzKTtcbiAgICB9XG4gIH07XG59IiwiaW1wb3J0IHsgS0VZV09SRF9MSU1JVCB9IGZyb20gJy4vY29uc3RhbnRzJztcbnZhciBNRVRBREFUQV9NT0RFTCA9IHtcbiAgc2VydmljZToge1xuICAgIG5hbWU6IFtLRVlXT1JEX0xJTUlULCB0cnVlXSxcbiAgICB2ZXJzaW9uOiB0cnVlLFxuICAgIGFnZW50OiB7XG4gICAgICB2ZXJzaW9uOiBbS0VZV09SRF9MSU1JVCwgdHJ1ZV1cbiAgICB9LFxuICAgIGVudmlyb25tZW50OiB0cnVlXG4gIH0sXG4gIGxhYmVsczoge1xuICAgICcqJzogdHJ1ZVxuICB9XG59O1xudmFyIFJFU1BPTlNFX01PREVMID0ge1xuICAnKic6IHRydWUsXG4gIGhlYWRlcnM6IHtcbiAgICAnKic6IHRydWVcbiAgfVxufTtcbnZhciBERVNUSU5BVElPTl9NT0RFTCA9IHtcbiAgYWRkcmVzczogW0tFWVdPUkRfTElNSVRdLFxuICBzZXJ2aWNlOiB7XG4gICAgJyonOiBbS0VZV09SRF9MSU1JVCwgdHJ1ZV1cbiAgfVxufTtcbnZhciBDT05URVhUX01PREVMID0ge1xuICB1c2VyOiB7XG4gICAgaWQ6IHRydWUsXG4gICAgZW1haWw6IHRydWUsXG4gICAgdXNlcm5hbWU6IHRydWVcbiAgfSxcbiAgdGFnczoge1xuICAgICcqJzogdHJ1ZVxuICB9LFxuICBodHRwOiB7XG4gICAgcmVzcG9uc2U6IFJFU1BPTlNFX01PREVMXG4gIH0sXG4gIGRlc3RpbmF0aW9uOiBERVNUSU5BVElPTl9NT0RFTCxcbiAgcmVzcG9uc2U6IFJFU1BPTlNFX01PREVMXG59O1xudmFyIFNQQU5fTU9ERUwgPSB7XG4gIG5hbWU6IFtLRVlXT1JEX0xJTUlULCB0cnVlXSxcbiAgdHlwZTogW0tFWVdPUkRfTElNSVQsIHRydWVdLFxuICBpZDogW0tFWVdPUkRfTElNSVQsIHRydWVdLFxuICB0cmFjZV9pZDogW0tFWVdPUkRfTElNSVQsIHRydWVdLFxuICBwYXJlbnRfaWQ6IFtLRVlXT1JEX0xJTUlULCB0cnVlXSxcbiAgdHJhbnNhY3Rpb25faWQ6IFtLRVlXT1JEX0xJTUlULCB0cnVlXSxcbiAgc3VidHlwZTogdHJ1ZSxcbiAgYWN0aW9uOiB0cnVlLFxuICBjb250ZXh0OiBDT05URVhUX01PREVMXG59O1xudmFyIFRSQU5TQUNUSU9OX01PREVMID0ge1xuICBuYW1lOiB0cnVlLFxuICBwYXJlbnRfaWQ6IHRydWUsXG4gIHR5cGU6IFtLRVlXT1JEX0xJTUlULCB0cnVlXSxcbiAgaWQ6IFtLRVlXT1JEX0xJTUlULCB0cnVlXSxcbiAgdHJhY2VfaWQ6IFtLRVlXT1JEX0xJTUlULCB0cnVlXSxcbiAgc3Bhbl9jb3VudDoge1xuICAgIHN0YXJ0ZWQ6IFtLRVlXT1JEX0xJTUlULCB0cnVlXVxuICB9LFxuICBjb250ZXh0OiBDT05URVhUX01PREVMXG59O1xudmFyIEVSUk9SX01PREVMID0ge1xuICBpZDogW0tFWVdPUkRfTElNSVQsIHRydWVdLFxuICB0cmFjZV9pZDogdHJ1ZSxcbiAgdHJhbnNhY3Rpb25faWQ6IHRydWUsXG4gIHBhcmVudF9pZDogdHJ1ZSxcbiAgY3VscHJpdDogdHJ1ZSxcbiAgZXhjZXB0aW9uOiB7XG4gICAgdHlwZTogdHJ1ZVxuICB9LFxuICB0cmFuc2FjdGlvbjoge1xuICAgIHR5cGU6IHRydWVcbiAgfSxcbiAgY29udGV4dDogQ09OVEVYVF9NT0RFTFxufTtcblxuZnVuY3Rpb24gdHJ1bmNhdGUodmFsdWUsIGxpbWl0LCByZXF1aXJlZCwgcGxhY2Vob2xkZXIpIHtcbiAgaWYgKGxpbWl0ID09PSB2b2lkIDApIHtcbiAgICBsaW1pdCA9IEtFWVdPUkRfTElNSVQ7XG4gIH1cblxuICBpZiAocmVxdWlyZWQgPT09IHZvaWQgMCkge1xuICAgIHJlcXVpcmVkID0gZmFsc2U7XG4gIH1cblxuICBpZiAocGxhY2Vob2xkZXIgPT09IHZvaWQgMCkge1xuICAgIHBsYWNlaG9sZGVyID0gJ04vQSc7XG4gIH1cblxuICBpZiAocmVxdWlyZWQgJiYgaXNFbXB0eSh2YWx1ZSkpIHtcbiAgICB2YWx1ZSA9IHBsYWNlaG9sZGVyO1xuICB9XG5cbiAgaWYgKHR5cGVvZiB2YWx1ZSA9PT0gJ3N0cmluZycpIHtcbiAgICByZXR1cm4gdmFsdWUuc3Vic3RyaW5nKDAsIGxpbWl0KTtcbiAgfVxuXG4gIHJldHVybiB2YWx1ZTtcbn1cblxuZnVuY3Rpb24gaXNFbXB0eSh2YWx1ZSkge1xuICByZXR1cm4gdmFsdWUgPT0gbnVsbCB8fCB2YWx1ZSA9PT0gJycgfHwgdHlwZW9mIHZhbHVlID09PSAndW5kZWZpbmVkJztcbn1cblxuZnVuY3Rpb24gcmVwbGFjZVZhbHVlKHRhcmdldCwga2V5LCBjdXJyTW9kZWwpIHtcbiAgdmFyIHZhbHVlID0gdHJ1bmNhdGUodGFyZ2V0W2tleV0sIGN1cnJNb2RlbFswXSwgY3Vyck1vZGVsWzFdKTtcblxuICBpZiAoaXNFbXB0eSh2YWx1ZSkpIHtcbiAgICBkZWxldGUgdGFyZ2V0W2tleV07XG4gICAgcmV0dXJuO1xuICB9XG5cbiAgdGFyZ2V0W2tleV0gPSB2YWx1ZTtcbn1cblxuZnVuY3Rpb24gdHJ1bmNhdGVNb2RlbChtb2RlbCwgdGFyZ2V0LCBjaGlsZFRhcmdldCkge1xuICBpZiAobW9kZWwgPT09IHZvaWQgMCkge1xuICAgIG1vZGVsID0ge307XG4gIH1cblxuICBpZiAoY2hpbGRUYXJnZXQgPT09IHZvaWQgMCkge1xuICAgIGNoaWxkVGFyZ2V0ID0gdGFyZ2V0O1xuICB9XG5cbiAgdmFyIGtleXMgPSBPYmplY3Qua2V5cyhtb2RlbCk7XG4gIHZhciBlbXB0eUFyciA9IFtdO1xuXG4gIHZhciBfbG9vcCA9IGZ1bmN0aW9uIF9sb29wKGkpIHtcbiAgICB2YXIgY3VycktleSA9IGtleXNbaV07XG4gICAgdmFyIGN1cnJNb2RlbCA9IG1vZGVsW2N1cnJLZXldID09PSB0cnVlID8gZW1wdHlBcnIgOiBtb2RlbFtjdXJyS2V5XTtcblxuICAgIGlmICghQXJyYXkuaXNBcnJheShjdXJyTW9kZWwpKSB7XG4gICAgICB0cnVuY2F0ZU1vZGVsKGN1cnJNb2RlbCwgdGFyZ2V0LCBjaGlsZFRhcmdldFtjdXJyS2V5XSk7XG4gICAgfSBlbHNlIHtcbiAgICAgIGlmIChjdXJyS2V5ID09PSAnKicpIHtcbiAgICAgICAgT2JqZWN0LmtleXMoY2hpbGRUYXJnZXQpLmZvckVhY2goZnVuY3Rpb24gKGtleSkge1xuICAgICAgICAgIHJldHVybiByZXBsYWNlVmFsdWUoY2hpbGRUYXJnZXQsIGtleSwgY3Vyck1vZGVsKTtcbiAgICAgICAgfSk7XG4gICAgICB9IGVsc2Uge1xuICAgICAgICByZXBsYWNlVmFsdWUoY2hpbGRUYXJnZXQsIGN1cnJLZXksIGN1cnJNb2RlbCk7XG4gICAgICB9XG4gICAgfVxuICB9O1xuXG4gIGZvciAodmFyIGkgPSAwOyBpIDwga2V5cy5sZW5ndGg7IGkrKykge1xuICAgIF9sb29wKGkpO1xuICB9XG5cbiAgcmV0dXJuIHRhcmdldDtcbn1cblxuZXhwb3J0IHsgdHJ1bmNhdGUsIHRydW5jYXRlTW9kZWwsIFNQQU5fTU9ERUwsIFRSQU5TQUNUSU9OX01PREVMLCBFUlJPUl9NT0RFTCwgTUVUQURBVEFfTU9ERUwsIFJFU1BPTlNFX01PREVMIH07IiwiaW1wb3J0IHsgaXNCcm93c2VyIH0gZnJvbSAnLi91dGlscyc7XG5cbmZ1bmN0aW9uIGlzRGVmYXVsdFBvcnQocG9ydCwgcHJvdG9jb2wpIHtcbiAgc3dpdGNoIChwcm90b2NvbCkge1xuICAgIGNhc2UgJ2h0dHA6JzpcbiAgICAgIHJldHVybiBwb3J0ID09PSAnODAnO1xuXG4gICAgY2FzZSAnaHR0cHM6JzpcbiAgICAgIHJldHVybiBwb3J0ID09PSAnNDQzJztcbiAgfVxuXG4gIHJldHVybiB0cnVlO1xufVxuXG52YXIgUlVMRVMgPSBbWycjJywgJ2hhc2gnXSwgWyc/JywgJ3F1ZXJ5J10sIFsnLycsICdwYXRoJ10sIFsnQCcsICdhdXRoJywgMV0sIFtOYU4sICdob3N0JywgdW5kZWZpbmVkLCAxXV07XG52YXIgUFJPVE9DT0xfUkVHRVggPSAvXihbYS16XVthLXowLTkuKy1dKjopPyhcXC9cXC8pPyhbXFxTXFxzXSopL2k7XG5leHBvcnQgdmFyIFVybCA9IGZ1bmN0aW9uICgpIHtcbiAgZnVuY3Rpb24gVXJsKHVybCkge1xuICAgIHZhciBfdGhpcyRleHRyYWN0UHJvdG9jb2wgPSB0aGlzLmV4dHJhY3RQcm90b2NvbCh1cmwgfHwgJycpLFxuICAgICAgICBwcm90b2NvbCA9IF90aGlzJGV4dHJhY3RQcm90b2NvbC5wcm90b2NvbCxcbiAgICAgICAgYWRkcmVzcyA9IF90aGlzJGV4dHJhY3RQcm90b2NvbC5hZGRyZXNzLFxuICAgICAgICBzbGFzaGVzID0gX3RoaXMkZXh0cmFjdFByb3RvY29sLnNsYXNoZXM7XG5cbiAgICB2YXIgcmVsYXRpdmUgPSAhcHJvdG9jb2wgJiYgIXNsYXNoZXM7XG4gICAgdmFyIGxvY2F0aW9uID0gdGhpcy5nZXRMb2NhdGlvbigpO1xuICAgIHZhciBpbnN0cnVjdGlvbnMgPSBSVUxFUy5zbGljZSgpO1xuICAgIGFkZHJlc3MgPSBhZGRyZXNzLnJlcGxhY2UoJ1xcXFwnLCAnLycpO1xuXG4gICAgaWYgKCFzbGFzaGVzKSB7XG4gICAgICBpbnN0cnVjdGlvbnNbMl0gPSBbTmFOLCAncGF0aCddO1xuICAgIH1cblxuICAgIHZhciBpbmRleDtcblxuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgaW5zdHJ1Y3Rpb25zLmxlbmd0aDsgaSsrKSB7XG4gICAgICB2YXIgaW5zdHJ1Y3Rpb24gPSBpbnN0cnVjdGlvbnNbaV07XG4gICAgICB2YXIgcGFyc2UgPSBpbnN0cnVjdGlvblswXTtcbiAgICAgIHZhciBrZXkgPSBpbnN0cnVjdGlvblsxXTtcblxuICAgICAgaWYgKHR5cGVvZiBwYXJzZSA9PT0gJ3N0cmluZycpIHtcbiAgICAgICAgaW5kZXggPSBhZGRyZXNzLmluZGV4T2YocGFyc2UpO1xuXG4gICAgICAgIGlmICh+aW5kZXgpIHtcbiAgICAgICAgICB2YXIgaW5zdExlbmd0aCA9IGluc3RydWN0aW9uWzJdO1xuXG4gICAgICAgICAgaWYgKGluc3RMZW5ndGgpIHtcbiAgICAgICAgICAgIHZhciBuZXdJbmRleCA9IGFkZHJlc3MubGFzdEluZGV4T2YocGFyc2UpO1xuICAgICAgICAgICAgaW5kZXggPSBNYXRoLm1heChpbmRleCwgbmV3SW5kZXgpO1xuICAgICAgICAgICAgdGhpc1trZXldID0gYWRkcmVzcy5zbGljZSgwLCBpbmRleCk7XG4gICAgICAgICAgICBhZGRyZXNzID0gYWRkcmVzcy5zbGljZShpbmRleCArIGluc3RMZW5ndGgpO1xuICAgICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgICB0aGlzW2tleV0gPSBhZGRyZXNzLnNsaWNlKGluZGV4KTtcbiAgICAgICAgICAgIGFkZHJlc3MgPSBhZGRyZXNzLnNsaWNlKDAsIGluZGV4KTtcbiAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICAgIH0gZWxzZSB7XG4gICAgICAgIHRoaXNba2V5XSA9IGFkZHJlc3M7XG4gICAgICAgIGFkZHJlc3MgPSAnJztcbiAgICAgIH1cblxuICAgICAgdGhpc1trZXldID0gdGhpc1trZXldIHx8IChyZWxhdGl2ZSAmJiBpbnN0cnVjdGlvblszXSA/IGxvY2F0aW9uW2tleV0gfHwgJycgOiAnJyk7XG4gICAgICBpZiAoaW5zdHJ1Y3Rpb25bM10pIHRoaXNba2V5XSA9IHRoaXNba2V5XS50b0xvd2VyQ2FzZSgpO1xuICAgIH1cblxuICAgIGlmIChyZWxhdGl2ZSAmJiB0aGlzLnBhdGguY2hhckF0KDApICE9PSAnLycpIHtcbiAgICAgIHRoaXMucGF0aCA9ICcvJyArIHRoaXMucGF0aDtcbiAgICB9XG5cbiAgICB0aGlzLnJlbGF0aXZlID0gcmVsYXRpdmU7XG4gICAgdGhpcy5wcm90b2NvbCA9IHByb3RvY29sIHx8IGxvY2F0aW9uLnByb3RvY29sO1xuICAgIHRoaXMuaG9zdG5hbWUgPSB0aGlzLmhvc3Q7XG4gICAgdGhpcy5wb3J0ID0gJyc7XG5cbiAgICBpZiAoLzpcXGQrJC8udGVzdCh0aGlzLmhvc3QpKSB7XG4gICAgICB2YXIgdmFsdWUgPSB0aGlzLmhvc3Quc3BsaXQoJzonKTtcbiAgICAgIHZhciBwb3J0ID0gdmFsdWUucG9wKCk7XG4gICAgICB2YXIgaG9zdG5hbWUgPSB2YWx1ZS5qb2luKCc6Jyk7XG5cbiAgICAgIGlmIChpc0RlZmF1bHRQb3J0KHBvcnQsIHRoaXMucHJvdG9jb2wpKSB7XG4gICAgICAgIHRoaXMuaG9zdCA9IGhvc3RuYW1lO1xuICAgICAgfSBlbHNlIHtcbiAgICAgICAgdGhpcy5wb3J0ID0gcG9ydDtcbiAgICAgIH1cblxuICAgICAgdGhpcy5ob3N0bmFtZSA9IGhvc3RuYW1lO1xuICAgIH1cblxuICAgIHRoaXMub3JpZ2luID0gdGhpcy5wcm90b2NvbCAmJiB0aGlzLmhvc3QgJiYgdGhpcy5wcm90b2NvbCAhPT0gJ2ZpbGU6JyA/IHRoaXMucHJvdG9jb2wgKyAnLy8nICsgdGhpcy5ob3N0IDogJ251bGwnO1xuICAgIHRoaXMuaHJlZiA9IHRoaXMudG9TdHJpbmcoKTtcbiAgfVxuXG4gIHZhciBfcHJvdG8gPSBVcmwucHJvdG90eXBlO1xuXG4gIF9wcm90by50b1N0cmluZyA9IGZ1bmN0aW9uIHRvU3RyaW5nKCkge1xuICAgIHZhciByZXN1bHQgPSB0aGlzLnByb3RvY29sO1xuICAgIHJlc3VsdCArPSAnLy8nO1xuXG4gICAgaWYgKHRoaXMuYXV0aCkge1xuICAgICAgdmFyIFJFREFDVEVEID0gJ1tSRURBQ1RFRF0nO1xuICAgICAgdmFyIHVzZXJwYXNzID0gdGhpcy5hdXRoLnNwbGl0KCc6Jyk7XG4gICAgICB2YXIgdXNlcm5hbWUgPSB1c2VycGFzc1swXSA/IFJFREFDVEVEIDogJyc7XG4gICAgICB2YXIgcGFzc3dvcmQgPSB1c2VycGFzc1sxXSA/ICc6JyArIFJFREFDVEVEIDogJyc7XG4gICAgICByZXN1bHQgKz0gdXNlcm5hbWUgKyBwYXNzd29yZCArICdAJztcbiAgICB9XG5cbiAgICByZXN1bHQgKz0gdGhpcy5ob3N0O1xuICAgIHJlc3VsdCArPSB0aGlzLnBhdGg7XG4gICAgcmVzdWx0ICs9IHRoaXMucXVlcnk7XG4gICAgcmVzdWx0ICs9IHRoaXMuaGFzaDtcbiAgICByZXR1cm4gcmVzdWx0O1xuICB9O1xuXG4gIF9wcm90by5nZXRMb2NhdGlvbiA9IGZ1bmN0aW9uIGdldExvY2F0aW9uKCkge1xuICAgIHZhciBnbG9iYWxWYXIgPSB7fTtcblxuICAgIGlmIChpc0Jyb3dzZXIpIHtcbiAgICAgIGdsb2JhbFZhciA9IHdpbmRvdztcbiAgICB9XG5cbiAgICByZXR1cm4gZ2xvYmFsVmFyLmxvY2F0aW9uO1xuICB9O1xuXG4gIF9wcm90by5leHRyYWN0UHJvdG9jb2wgPSBmdW5jdGlvbiBleHRyYWN0UHJvdG9jb2wodXJsKSB7XG4gICAgdmFyIG1hdGNoID0gUFJPVE9DT0xfUkVHRVguZXhlYyh1cmwpO1xuICAgIHJldHVybiB7XG4gICAgICBwcm90b2NvbDogbWF0Y2hbMV0gPyBtYXRjaFsxXS50b0xvd2VyQ2FzZSgpIDogJycsXG4gICAgICBzbGFzaGVzOiAhIW1hdGNoWzJdLFxuICAgICAgYWRkcmVzczogbWF0Y2hbM11cbiAgICB9O1xuICB9O1xuXG4gIHJldHVybiBVcmw7XG59KCk7XG5leHBvcnQgZnVuY3Rpb24gc2x1Z2lmeVVybCh1cmxTdHIsIGRlcHRoKSB7XG4gIGlmIChkZXB0aCA9PT0gdm9pZCAwKSB7XG4gICAgZGVwdGggPSAyO1xuICB9XG5cbiAgdmFyIHBhcnNlZFVybCA9IG5ldyBVcmwodXJsU3RyKTtcbiAgdmFyIHF1ZXJ5ID0gcGFyc2VkVXJsLnF1ZXJ5LFxuICAgICAgcGF0aCA9IHBhcnNlZFVybC5wYXRoO1xuICB2YXIgcGF0aFBhcnRzID0gcGF0aC5zdWJzdHJpbmcoMSkuc3BsaXQoJy8nKTtcbiAgdmFyIHJlZGFjdFN0cmluZyA9ICc6aWQnO1xuICB2YXIgd2lsZGNhcmQgPSAnKic7XG4gIHZhciBzcGVjaWFsQ2hhcnNSZWdleCA9IC9cXFd8Xy9nO1xuICB2YXIgZGlnaXRzUmVnZXggPSAvWzAtOV0vZztcbiAgdmFyIGxvd2VyQ2FzZVJlZ2V4ID0gL1thLXpdL2c7XG4gIHZhciB1cHBlckNhc2VSZWdleCA9IC9bQS1aXS9nO1xuICB2YXIgcmVkYWN0ZWRQYXJ0cyA9IFtdO1xuICB2YXIgcmVkYWN0ZWRCZWZvcmUgPSBmYWxzZTtcblxuICBmb3IgKHZhciBpbmRleCA9IDA7IGluZGV4IDwgcGF0aFBhcnRzLmxlbmd0aDsgaW5kZXgrKykge1xuICAgIHZhciBwYXJ0ID0gcGF0aFBhcnRzW2luZGV4XTtcblxuICAgIGlmIChyZWRhY3RlZEJlZm9yZSB8fCBpbmRleCA+IGRlcHRoIC0gMSkge1xuICAgICAgaWYgKHBhcnQpIHtcbiAgICAgICAgcmVkYWN0ZWRQYXJ0cy5wdXNoKHdpbGRjYXJkKTtcbiAgICAgIH1cblxuICAgICAgYnJlYWs7XG4gICAgfVxuXG4gICAgdmFyIG51bWJlck9mU3BlY2lhbENoYXJzID0gKHBhcnQubWF0Y2goc3BlY2lhbENoYXJzUmVnZXgpIHx8IFtdKS5sZW5ndGg7XG5cbiAgICBpZiAobnVtYmVyT2ZTcGVjaWFsQ2hhcnMgPj0gMikge1xuICAgICAgcmVkYWN0ZWRQYXJ0cy5wdXNoKHJlZGFjdFN0cmluZyk7XG4gICAgICByZWRhY3RlZEJlZm9yZSA9IHRydWU7XG4gICAgICBjb250aW51ZTtcbiAgICB9XG5cbiAgICB2YXIgbnVtYmVyT2ZEaWdpdHMgPSAocGFydC5tYXRjaChkaWdpdHNSZWdleCkgfHwgW10pLmxlbmd0aDtcblxuICAgIGlmIChudW1iZXJPZkRpZ2l0cyA+IDMgfHwgcGFydC5sZW5ndGggPiAzICYmIG51bWJlck9mRGlnaXRzIC8gcGFydC5sZW5ndGggPj0gMC4zKSB7XG4gICAgICByZWRhY3RlZFBhcnRzLnB1c2gocmVkYWN0U3RyaW5nKTtcbiAgICAgIHJlZGFjdGVkQmVmb3JlID0gdHJ1ZTtcbiAgICAgIGNvbnRpbnVlO1xuICAgIH1cblxuICAgIHZhciBudW1iZXJvZlVwcGVyQ2FzZSA9IChwYXJ0Lm1hdGNoKHVwcGVyQ2FzZVJlZ2V4KSB8fCBbXSkubGVuZ3RoO1xuICAgIHZhciBudW1iZXJvZkxvd2VyQ2FzZSA9IChwYXJ0Lm1hdGNoKGxvd2VyQ2FzZVJlZ2V4KSB8fCBbXSkubGVuZ3RoO1xuICAgIHZhciBsb3dlckNhc2VSYXRlID0gbnVtYmVyb2ZMb3dlckNhc2UgLyBwYXJ0Lmxlbmd0aDtcbiAgICB2YXIgdXBwZXJDYXNlUmF0ZSA9IG51bWJlcm9mVXBwZXJDYXNlIC8gcGFydC5sZW5ndGg7XG5cbiAgICBpZiAocGFydC5sZW5ndGggPiA1ICYmICh1cHBlckNhc2VSYXRlID4gMC4zICYmIHVwcGVyQ2FzZVJhdGUgPCAwLjYgfHwgbG93ZXJDYXNlUmF0ZSA+IDAuMyAmJiBsb3dlckNhc2VSYXRlIDwgMC42KSkge1xuICAgICAgcmVkYWN0ZWRQYXJ0cy5wdXNoKHJlZGFjdFN0cmluZyk7XG4gICAgICByZWRhY3RlZEJlZm9yZSA9IHRydWU7XG4gICAgICBjb250aW51ZTtcbiAgICB9XG5cbiAgICBwYXJ0ICYmIHJlZGFjdGVkUGFydHMucHVzaChwYXJ0KTtcbiAgfVxuXG4gIHZhciByZWRhY3RlZCA9ICcvJyArIChyZWRhY3RlZFBhcnRzLmxlbmd0aCA+PSAyID8gcmVkYWN0ZWRQYXJ0cy5qb2luKCcvJykgOiByZWRhY3RlZFBhcnRzLmpvaW4oJycpKSArIChxdWVyeSA/ICc/e3F1ZXJ5fScgOiAnJyk7XG4gIHJldHVybiByZWRhY3RlZDtcbn0iLCJpbXBvcnQgeyBQcm9taXNlIH0gZnJvbSAnLi9wb2x5ZmlsbHMnO1xudmFyIHNsaWNlID0gW10uc2xpY2U7XG52YXIgaXNCcm93c2VyID0gdHlwZW9mIHdpbmRvdyAhPT0gJ3VuZGVmaW5lZCc7XG52YXIgUEVSRiA9IGlzQnJvd3NlciAmJiB0eXBlb2YgcGVyZm9ybWFuY2UgIT09ICd1bmRlZmluZWQnID8gcGVyZm9ybWFuY2UgOiB7fTtcblxuZnVuY3Rpb24gaXNDT1JTU3VwcG9ydGVkKCkge1xuICB2YXIgeGhyID0gbmV3IHdpbmRvdy5YTUxIdHRwUmVxdWVzdCgpO1xuICByZXR1cm4gJ3dpdGhDcmVkZW50aWFscycgaW4geGhyO1xufVxuXG52YXIgYnl0ZVRvSGV4ID0gW107XG5cbmZvciAodmFyIGkgPSAwOyBpIDwgMjU2OyArK2kpIHtcbiAgYnl0ZVRvSGV4W2ldID0gKGkgKyAweDEwMCkudG9TdHJpbmcoMTYpLnN1YnN0cigxKTtcbn1cblxuZnVuY3Rpb24gYnl0ZXNUb0hleChidWZmZXIpIHtcbiAgdmFyIGhleE9jdGV0cyA9IFtdO1xuXG4gIGZvciAodmFyIF9pID0gMDsgX2kgPCBidWZmZXIubGVuZ3RoOyBfaSsrKSB7XG4gICAgaGV4T2N0ZXRzLnB1c2goYnl0ZVRvSGV4W2J1ZmZlcltfaV1dKTtcbiAgfVxuXG4gIHJldHVybiBoZXhPY3RldHMuam9pbignJyk7XG59XG5cbnZhciBkZXN0aW5hdGlvbiA9IG5ldyBVaW50OEFycmF5KDE2KTtcblxuZnVuY3Rpb24gcm5nKCkge1xuICBpZiAodHlwZW9mIGNyeXB0byAhPSAndW5kZWZpbmVkJyAmJiB0eXBlb2YgY3J5cHRvLmdldFJhbmRvbVZhbHVlcyA9PSAnZnVuY3Rpb24nKSB7XG4gICAgcmV0dXJuIGNyeXB0by5nZXRSYW5kb21WYWx1ZXMoZGVzdGluYXRpb24pO1xuICB9IGVsc2UgaWYgKHR5cGVvZiBtc0NyeXB0byAhPSAndW5kZWZpbmVkJyAmJiB0eXBlb2YgbXNDcnlwdG8uZ2V0UmFuZG9tVmFsdWVzID09ICdmdW5jdGlvbicpIHtcbiAgICByZXR1cm4gbXNDcnlwdG8uZ2V0UmFuZG9tVmFsdWVzKGRlc3RpbmF0aW9uKTtcbiAgfVxuXG4gIHJldHVybiBkZXN0aW5hdGlvbjtcbn1cblxuZnVuY3Rpb24gZ2VuZXJhdGVSYW5kb21JZChsZW5ndGgpIHtcbiAgdmFyIGlkID0gYnl0ZXNUb0hleChybmcoKSk7XG4gIHJldHVybiBpZC5zdWJzdHIoMCwgbGVuZ3RoKTtcbn1cblxuZnVuY3Rpb24gZ2V0RHRIZWFkZXJWYWx1ZShzcGFuKSB7XG4gIHZhciBkdFZlcnNpb24gPSAnMDAnO1xuICB2YXIgZHRVblNhbXBsZWRGbGFncyA9ICcwMCc7XG4gIHZhciBkdFNhbXBsZWRGbGFncyA9ICcwMSc7XG5cbiAgaWYgKHNwYW4gJiYgc3Bhbi50cmFjZUlkICYmIHNwYW4uaWQgJiYgc3Bhbi5wYXJlbnRJZCkge1xuICAgIHZhciBmbGFncyA9IHNwYW4uc2FtcGxlZCA/IGR0U2FtcGxlZEZsYWdzIDogZHRVblNhbXBsZWRGbGFncztcbiAgICB2YXIgaWQgPSBzcGFuLnNhbXBsZWQgPyBzcGFuLmlkIDogc3Bhbi5wYXJlbnRJZDtcbiAgICByZXR1cm4gZHRWZXJzaW9uICsgJy0nICsgc3Bhbi50cmFjZUlkICsgJy0nICsgaWQgKyAnLScgKyBmbGFncztcbiAgfVxufVxuXG5mdW5jdGlvbiBwYXJzZUR0SGVhZGVyVmFsdWUodmFsdWUpIHtcbiAgdmFyIHBhcnNlZCA9IC9eKFtcXGRhLWZdezJ9KS0oW1xcZGEtZl17MzJ9KS0oW1xcZGEtZl17MTZ9KS0oW1xcZGEtZl17Mn0pJC8uZXhlYyh2YWx1ZSk7XG5cbiAgaWYgKHBhcnNlZCkge1xuICAgIHZhciBmbGFncyA9IHBhcnNlZFs0XTtcbiAgICB2YXIgc2FtcGxlZCA9IGZsYWdzICE9PSAnMDAnO1xuICAgIHJldHVybiB7XG4gICAgICB0cmFjZUlkOiBwYXJzZWRbMl0sXG4gICAgICBpZDogcGFyc2VkWzNdLFxuICAgICAgc2FtcGxlZDogc2FtcGxlZFxuICAgIH07XG4gIH1cbn1cblxuZnVuY3Rpb24gaXNEdEhlYWRlclZhbGlkKGhlYWRlcikge1xuICByZXR1cm4gL15bXFxkYS1mXXsyfS1bXFxkYS1mXXszMn0tW1xcZGEtZl17MTZ9LVtcXGRhLWZdezJ9JC8udGVzdChoZWFkZXIpICYmIGhlYWRlci5zbGljZSgzLCAzNSkgIT09ICcwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMCcgJiYgaGVhZGVyLnNsaWNlKDM2LCA1MikgIT09ICcwMDAwMDAwMDAwMDAwMDAwJztcbn1cblxuZnVuY3Rpb24gZ2V0VFNIZWFkZXJWYWx1ZShfcmVmKSB7XG4gIHZhciBzYW1wbGVSYXRlID0gX3JlZi5zYW1wbGVSYXRlO1xuXG4gIGlmICh0eXBlb2Ygc2FtcGxlUmF0ZSAhPT0gJ251bWJlcicgfHwgU3RyaW5nKHNhbXBsZVJhdGUpLmxlbmd0aCA+IDI1Nikge1xuICAgIHJldHVybjtcbiAgfVxuXG4gIHZhciBOQU1FU1BBQ0UgPSAnZXMnO1xuICB2YXIgU0VQQVJBVE9SID0gJz0nO1xuICByZXR1cm4gXCJcIiArIE5BTUVTUEFDRSArIFNFUEFSQVRPUiArIFwiczpcIiArIHNhbXBsZVJhdGU7XG59XG5cbmZ1bmN0aW9uIHNldFJlcXVlc3RIZWFkZXIodGFyZ2V0LCBuYW1lLCB2YWx1ZSkge1xuICBpZiAodHlwZW9mIHRhcmdldC5zZXRSZXF1ZXN0SGVhZGVyID09PSAnZnVuY3Rpb24nKSB7XG4gICAgdGFyZ2V0LnNldFJlcXVlc3RIZWFkZXIobmFtZSwgdmFsdWUpO1xuICB9IGVsc2UgaWYgKHRhcmdldC5oZWFkZXJzICYmIHR5cGVvZiB0YXJnZXQuaGVhZGVycy5hcHBlbmQgPT09ICdmdW5jdGlvbicpIHtcbiAgICB0YXJnZXQuaGVhZGVycy5hcHBlbmQobmFtZSwgdmFsdWUpO1xuICB9IGVsc2Uge1xuICAgIHRhcmdldFtuYW1lXSA9IHZhbHVlO1xuICB9XG59XG5cbmZ1bmN0aW9uIGNoZWNrU2FtZU9yaWdpbihzb3VyY2UsIHRhcmdldCkge1xuICB2YXIgaXNTYW1lID0gZmFsc2U7XG5cbiAgaWYgKHR5cGVvZiB0YXJnZXQgPT09ICdzdHJpbmcnKSB7XG4gICAgaXNTYW1lID0gc291cmNlID09PSB0YXJnZXQ7XG4gIH0gZWxzZSBpZiAodGFyZ2V0ICYmIHR5cGVvZiB0YXJnZXQudGVzdCA9PT0gJ2Z1bmN0aW9uJykge1xuICAgIGlzU2FtZSA9IHRhcmdldC50ZXN0KHNvdXJjZSk7XG4gIH0gZWxzZSBpZiAoQXJyYXkuaXNBcnJheSh0YXJnZXQpKSB7XG4gICAgdGFyZ2V0LmZvckVhY2goZnVuY3Rpb24gKHQpIHtcbiAgICAgIGlmICghaXNTYW1lKSB7XG4gICAgICAgIGlzU2FtZSA9IGNoZWNrU2FtZU9yaWdpbihzb3VyY2UsIHQpO1xuICAgICAgfVxuICAgIH0pO1xuICB9XG5cbiAgcmV0dXJuIGlzU2FtZTtcbn1cblxuZnVuY3Rpb24gaXNQbGF0Zm9ybVN1cHBvcnRlZCgpIHtcbiAgcmV0dXJuIGlzQnJvd3NlciAmJiB0eXBlb2YgU2V0ID09PSAnZnVuY3Rpb24nICYmIHR5cGVvZiBKU09OLnN0cmluZ2lmeSA9PT0gJ2Z1bmN0aW9uJyAmJiBQRVJGICYmIHR5cGVvZiBQRVJGLm5vdyA9PT0gJ2Z1bmN0aW9uJyAmJiBpc0NPUlNTdXBwb3J0ZWQoKTtcbn1cblxuZnVuY3Rpb24gc2V0TGFiZWwoa2V5LCB2YWx1ZSwgb2JqKSB7XG4gIGlmICghb2JqIHx8ICFrZXkpIHJldHVybjtcbiAgdmFyIHNrZXkgPSByZW1vdmVJbnZhbGlkQ2hhcnMoa2V5KTtcbiAgdmFyIHZhbHVlVHlwZSA9IHR5cGVvZiB2YWx1ZTtcblxuICBpZiAodmFsdWUgIT0gdW5kZWZpbmVkICYmIHZhbHVlVHlwZSAhPT0gJ2Jvb2xlYW4nICYmIHZhbHVlVHlwZSAhPT0gJ251bWJlcicpIHtcbiAgICB2YWx1ZSA9IFN0cmluZyh2YWx1ZSk7XG4gIH1cblxuICBvYmpbc2tleV0gPSB2YWx1ZTtcbiAgcmV0dXJuIG9iajtcbn1cblxuZnVuY3Rpb24gZ2V0U2VydmVyVGltaW5nSW5mbyhzZXJ2ZXJUaW1pbmdFbnRyaWVzKSB7XG4gIGlmIChzZXJ2ZXJUaW1pbmdFbnRyaWVzID09PSB2b2lkIDApIHtcbiAgICBzZXJ2ZXJUaW1pbmdFbnRyaWVzID0gW107XG4gIH1cblxuICB2YXIgc2VydmVyVGltaW5nSW5mbyA9IFtdO1xuICB2YXIgZW50cnlTZXBhcmF0b3IgPSAnLCAnO1xuICB2YXIgdmFsdWVTZXBhcmF0b3IgPSAnOyc7XG5cbiAgZm9yICh2YXIgX2kyID0gMDsgX2kyIDwgc2VydmVyVGltaW5nRW50cmllcy5sZW5ndGg7IF9pMisrKSB7XG4gICAgdmFyIF9zZXJ2ZXJUaW1pbmdFbnRyaWVzJCA9IHNlcnZlclRpbWluZ0VudHJpZXNbX2kyXSxcbiAgICAgICAgbmFtZSA9IF9zZXJ2ZXJUaW1pbmdFbnRyaWVzJC5uYW1lLFxuICAgICAgICBkdXJhdGlvbiA9IF9zZXJ2ZXJUaW1pbmdFbnRyaWVzJC5kdXJhdGlvbixcbiAgICAgICAgZGVzY3JpcHRpb24gPSBfc2VydmVyVGltaW5nRW50cmllcyQuZGVzY3JpcHRpb247XG4gICAgdmFyIHRpbWluZ1ZhbHVlID0gbmFtZTtcblxuICAgIGlmIChkZXNjcmlwdGlvbikge1xuICAgICAgdGltaW5nVmFsdWUgKz0gdmFsdWVTZXBhcmF0b3IgKyAnZGVzYz0nICsgZGVzY3JpcHRpb247XG4gICAgfVxuXG4gICAgaWYgKGR1cmF0aW9uKSB7XG4gICAgICB0aW1pbmdWYWx1ZSArPSB2YWx1ZVNlcGFyYXRvciArICdkdXI9JyArIGR1cmF0aW9uO1xuICAgIH1cblxuICAgIHNlcnZlclRpbWluZ0luZm8ucHVzaCh0aW1pbmdWYWx1ZSk7XG4gIH1cblxuICByZXR1cm4gc2VydmVyVGltaW5nSW5mby5qb2luKGVudHJ5U2VwYXJhdG9yKTtcbn1cblxuZnVuY3Rpb24gZ2V0VGltZU9yaWdpbigpIHtcbiAgcmV0dXJuIFBFUkYudGltaW5nLmZldGNoU3RhcnQ7XG59XG5cbmZ1bmN0aW9uIHN0cmlwUXVlcnlTdHJpbmdGcm9tVXJsKHVybCkge1xuICByZXR1cm4gdXJsICYmIHVybC5zcGxpdCgnPycpWzBdO1xufVxuXG5mdW5jdGlvbiBpc09iamVjdCh2YWx1ZSkge1xuICByZXR1cm4gdmFsdWUgIT09IG51bGwgJiYgdHlwZW9mIHZhbHVlID09PSAnb2JqZWN0Jztcbn1cblxuZnVuY3Rpb24gaXNGdW5jdGlvbih2YWx1ZSkge1xuICByZXR1cm4gdHlwZW9mIHZhbHVlID09PSAnZnVuY3Rpb24nO1xufVxuXG5mdW5jdGlvbiBiYXNlRXh0ZW5kKGRzdCwgb2JqcywgZGVlcCkge1xuICBmb3IgKHZhciBpID0gMCwgaWkgPSBvYmpzLmxlbmd0aDsgaSA8IGlpOyArK2kpIHtcbiAgICB2YXIgb2JqID0gb2Jqc1tpXTtcbiAgICBpZiAoIWlzT2JqZWN0KG9iaikgJiYgIWlzRnVuY3Rpb24ob2JqKSkgY29udGludWU7XG4gICAgdmFyIGtleXMgPSBPYmplY3Qua2V5cyhvYmopO1xuXG4gICAgZm9yICh2YXIgaiA9IDAsIGpqID0ga2V5cy5sZW5ndGg7IGogPCBqajsgaisrKSB7XG4gICAgICB2YXIga2V5ID0ga2V5c1tqXTtcbiAgICAgIHZhciBzcmMgPSBvYmpba2V5XTtcblxuICAgICAgaWYgKGRlZXAgJiYgaXNPYmplY3Qoc3JjKSkge1xuICAgICAgICBpZiAoIWlzT2JqZWN0KGRzdFtrZXldKSkgZHN0W2tleV0gPSBBcnJheS5pc0FycmF5KHNyYykgPyBbXSA6IHt9O1xuICAgICAgICBiYXNlRXh0ZW5kKGRzdFtrZXldLCBbc3JjXSwgZmFsc2UpO1xuICAgICAgfSBlbHNlIHtcbiAgICAgICAgZHN0W2tleV0gPSBzcmM7XG4gICAgICB9XG4gICAgfVxuICB9XG5cbiAgcmV0dXJuIGRzdDtcbn1cblxuZnVuY3Rpb24gZ2V0RWxhc3RpY1NjcmlwdCgpIHtcbiAgaWYgKHR5cGVvZiBkb2N1bWVudCAhPT0gJ3VuZGVmaW5lZCcpIHtcbiAgICB2YXIgc2NyaXB0cyA9IGRvY3VtZW50LmdldEVsZW1lbnRzQnlUYWdOYW1lKCdzY3JpcHQnKTtcblxuICAgIGZvciAodmFyIGkgPSAwLCBsID0gc2NyaXB0cy5sZW5ndGg7IGkgPCBsOyBpKyspIHtcbiAgICAgIHZhciBzYyA9IHNjcmlwdHNbaV07XG5cbiAgICAgIGlmIChzYy5zcmMuaW5kZXhPZignZWxhc3RpYycpID4gMCkge1xuICAgICAgICByZXR1cm4gc2M7XG4gICAgICB9XG4gICAgfVxuICB9XG59XG5cbmZ1bmN0aW9uIGdldEN1cnJlbnRTY3JpcHQoKSB7XG4gIGlmICh0eXBlb2YgZG9jdW1lbnQgIT09ICd1bmRlZmluZWQnKSB7XG4gICAgdmFyIGN1cnJlbnRTY3JpcHQgPSBkb2N1bWVudC5jdXJyZW50U2NyaXB0O1xuXG4gICAgaWYgKCFjdXJyZW50U2NyaXB0KSB7XG4gICAgICByZXR1cm4gZ2V0RWxhc3RpY1NjcmlwdCgpO1xuICAgIH1cblxuICAgIHJldHVybiBjdXJyZW50U2NyaXB0O1xuICB9XG59XG5cbmZ1bmN0aW9uIGV4dGVuZChkc3QpIHtcbiAgcmV0dXJuIGJhc2VFeHRlbmQoZHN0LCBzbGljZS5jYWxsKGFyZ3VtZW50cywgMSksIGZhbHNlKTtcbn1cblxuZnVuY3Rpb24gbWVyZ2UoZHN0KSB7XG4gIHJldHVybiBiYXNlRXh0ZW5kKGRzdCwgc2xpY2UuY2FsbChhcmd1bWVudHMsIDEpLCB0cnVlKTtcbn1cblxuZnVuY3Rpb24gaXNVbmRlZmluZWQob2JqKSB7XG4gIHJldHVybiB0eXBlb2Ygb2JqID09PSAndW5kZWZpbmVkJztcbn1cblxuZnVuY3Rpb24gbm9vcCgpIHt9XG5cbmZ1bmN0aW9uIGZpbmQoYXJyYXksIHByZWRpY2F0ZSwgdGhpc0FyZykge1xuICBpZiAoYXJyYXkgPT0gbnVsbCkge1xuICAgIHRocm93IG5ldyBUeXBlRXJyb3IoJ2FycmF5IGlzIG51bGwgb3Igbm90IGRlZmluZWQnKTtcbiAgfVxuXG4gIHZhciBvID0gT2JqZWN0KGFycmF5KTtcbiAgdmFyIGxlbiA9IG8ubGVuZ3RoID4+PiAwO1xuXG4gIGlmICh0eXBlb2YgcHJlZGljYXRlICE9PSAnZnVuY3Rpb24nKSB7XG4gICAgdGhyb3cgbmV3IFR5cGVFcnJvcigncHJlZGljYXRlIG11c3QgYmUgYSBmdW5jdGlvbicpO1xuICB9XG5cbiAgdmFyIGsgPSAwO1xuXG4gIHdoaWxlIChrIDwgbGVuKSB7XG4gICAgdmFyIGtWYWx1ZSA9IG9ba107XG5cbiAgICBpZiAocHJlZGljYXRlLmNhbGwodGhpc0FyZywga1ZhbHVlLCBrLCBvKSkge1xuICAgICAgcmV0dXJuIGtWYWx1ZTtcbiAgICB9XG5cbiAgICBrKys7XG4gIH1cblxuICByZXR1cm4gdW5kZWZpbmVkO1xufVxuXG5mdW5jdGlvbiByZW1vdmVJbnZhbGlkQ2hhcnMoa2V5KSB7XG4gIHJldHVybiBrZXkucmVwbGFjZSgvWy4qXCJdL2csICdfJyk7XG59XG5cbmZ1bmN0aW9uIGdldExhdGVzdFNwYW4oc3BhbnMsIHR5cGVGaWx0ZXIpIHtcbiAgdmFyIGxhdGVzdFNwYW4gPSBudWxsO1xuXG4gIGZvciAodmFyIF9pMyA9IDA7IF9pMyA8IHNwYW5zLmxlbmd0aDsgX2kzKyspIHtcbiAgICB2YXIgc3BhbiA9IHNwYW5zW19pM107XG5cbiAgICBpZiAodHlwZUZpbHRlciAmJiB0eXBlRmlsdGVyKHNwYW4udHlwZSkgJiYgKCFsYXRlc3RTcGFuIHx8IGxhdGVzdFNwYW4uX2VuZCA8IHNwYW4uX2VuZCkpIHtcbiAgICAgIGxhdGVzdFNwYW4gPSBzcGFuO1xuICAgIH1cbiAgfVxuXG4gIHJldHVybiBsYXRlc3RTcGFuO1xufVxuXG5mdW5jdGlvbiBnZXRMYXRlc3ROb25YSFJTcGFuKHNwYW5zKSB7XG4gIHJldHVybiBnZXRMYXRlc3RTcGFuKHNwYW5zLCBmdW5jdGlvbiAodHlwZSkge1xuICAgIHJldHVybiBTdHJpbmcodHlwZSkuaW5kZXhPZignZXh0ZXJuYWwnKSA9PT0gLTE7XG4gIH0pO1xufVxuXG5mdW5jdGlvbiBnZXRMYXRlc3RYSFJTcGFuKHNwYW5zKSB7XG4gIHJldHVybiBnZXRMYXRlc3RTcGFuKHNwYW5zLCBmdW5jdGlvbiAodHlwZSkge1xuICAgIHJldHVybiBTdHJpbmcodHlwZSkuaW5kZXhPZignZXh0ZXJuYWwnKSAhPT0gLTE7XG4gIH0pO1xufVxuXG5mdW5jdGlvbiBnZXRFYXJsaWVzdFNwYW4oc3BhbnMpIHtcbiAgdmFyIGVhcmxpZXN0U3BhbiA9IHNwYW5zWzBdO1xuXG4gIGZvciAodmFyIF9pNCA9IDE7IF9pNCA8IHNwYW5zLmxlbmd0aDsgX2k0KyspIHtcbiAgICB2YXIgc3BhbiA9IHNwYW5zW19pNF07XG5cbiAgICBpZiAoZWFybGllc3RTcGFuLl9zdGFydCA+IHNwYW4uX3N0YXJ0KSB7XG4gICAgICBlYXJsaWVzdFNwYW4gPSBzcGFuO1xuICAgIH1cbiAgfVxuXG4gIHJldHVybiBlYXJsaWVzdFNwYW47XG59XG5cbmZ1bmN0aW9uIG5vdygpIHtcbiAgcmV0dXJuIFBFUkYubm93KCk7XG59XG5cbmZ1bmN0aW9uIGdldFRpbWUodGltZSkge1xuICByZXR1cm4gdHlwZW9mIHRpbWUgPT09ICdudW1iZXInICYmIHRpbWUgPj0gMCA/IHRpbWUgOiBub3coKTtcbn1cblxuZnVuY3Rpb24gZ2V0RHVyYXRpb24oc3RhcnQsIGVuZCkge1xuICBpZiAoaXNVbmRlZmluZWQoZW5kKSB8fCBpc1VuZGVmaW5lZChzdGFydCkpIHtcbiAgICByZXR1cm4gbnVsbDtcbiAgfVxuXG4gIHJldHVybiBwYXJzZUludChlbmQgLSBzdGFydCk7XG59XG5cbmZ1bmN0aW9uIHNjaGVkdWxlTWFjcm9UYXNrKGNhbGxiYWNrKSB7XG4gIHNldFRpbWVvdXQoY2FsbGJhY2ssIDApO1xufVxuXG5mdW5jdGlvbiBzY2hlZHVsZU1pY3JvVGFzayhjYWxsYmFjaykge1xuICBQcm9taXNlLnJlc29sdmUoKS50aGVuKGNhbGxiYWNrKTtcbn1cblxuZnVuY3Rpb24gaXNQZXJmVGltZWxpbmVTdXBwb3J0ZWQoKSB7XG4gIHJldHVybiB0eXBlb2YgUEVSRi5nZXRFbnRyaWVzQnlUeXBlID09PSAnZnVuY3Rpb24nO1xufVxuXG5mdW5jdGlvbiBpc1BlcmZUeXBlU3VwcG9ydGVkKHR5cGUpIHtcbiAgcmV0dXJuIHR5cGVvZiBQZXJmb3JtYW5jZU9ic2VydmVyICE9PSAndW5kZWZpbmVkJyAmJiBQZXJmb3JtYW5jZU9ic2VydmVyLnN1cHBvcnRlZEVudHJ5VHlwZXMgJiYgUGVyZm9ybWFuY2VPYnNlcnZlci5zdXBwb3J0ZWRFbnRyeVR5cGVzLmluZGV4T2YodHlwZSkgPj0gMDtcbn1cblxuZnVuY3Rpb24gaXNCZWFjb25JbnNwZWN0aW9uRW5hYmxlZCgpIHtcbiAgdmFyIGZsYWdOYW1lID0gJ19lbGFzdGljX2luc3BlY3RfYmVhY29uXyc7XG5cbiAgaWYgKHNlc3Npb25TdG9yYWdlLmdldEl0ZW0oZmxhZ05hbWUpICE9IG51bGwpIHtcbiAgICByZXR1cm4gdHJ1ZTtcbiAgfVxuXG4gIGlmICghd2luZG93LlVSTCB8fCAhd2luZG93LlVSTFNlYXJjaFBhcmFtcykge1xuICAgIHJldHVybiBmYWxzZTtcbiAgfVxuXG4gIHRyeSB7XG4gICAgdmFyIHBhcnNlZFVybCA9IG5ldyBVUkwod2luZG93LmxvY2F0aW9uLmhyZWYpO1xuICAgIHZhciBpc0ZsYWdTZXQgPSBwYXJzZWRVcmwuc2VhcmNoUGFyYW1zLmhhcyhmbGFnTmFtZSk7XG5cbiAgICBpZiAoaXNGbGFnU2V0KSB7XG4gICAgICBzZXNzaW9uU3RvcmFnZS5zZXRJdGVtKGZsYWdOYW1lLCB0cnVlKTtcbiAgICB9XG5cbiAgICByZXR1cm4gaXNGbGFnU2V0O1xuICB9IGNhdGNoIChlKSB7fVxuXG4gIHJldHVybiBmYWxzZTtcbn1cblxuZXhwb3J0IHsgZXh0ZW5kLCBtZXJnZSwgaXNVbmRlZmluZWQsIG5vb3AsIGJhc2VFeHRlbmQsIGJ5dGVzVG9IZXgsIGlzQ09SU1N1cHBvcnRlZCwgaXNPYmplY3QsIGlzRnVuY3Rpb24sIGlzUGxhdGZvcm1TdXBwb3J0ZWQsIGlzRHRIZWFkZXJWYWxpZCwgcGFyc2VEdEhlYWRlclZhbHVlLCBnZXRTZXJ2ZXJUaW1pbmdJbmZvLCBnZXREdEhlYWRlclZhbHVlLCBnZXRUU0hlYWRlclZhbHVlLCBnZXRDdXJyZW50U2NyaXB0LCBnZXRFbGFzdGljU2NyaXB0LCBnZXRUaW1lT3JpZ2luLCBnZW5lcmF0ZVJhbmRvbUlkLCBnZXRFYXJsaWVzdFNwYW4sIGdldExhdGVzdE5vblhIUlNwYW4sIGdldExhdGVzdFhIUlNwYW4sIGdldER1cmF0aW9uLCBnZXRUaW1lLCBub3csIHJuZywgY2hlY2tTYW1lT3JpZ2luLCBzY2hlZHVsZU1hY3JvVGFzaywgc2NoZWR1bGVNaWNyb1Rhc2ssIHNldExhYmVsLCBzZXRSZXF1ZXN0SGVhZGVyLCBzdHJpcFF1ZXJ5U3RyaW5nRnJvbVVybCwgZmluZCwgcmVtb3ZlSW52YWxpZENoYXJzLCBQRVJGLCBpc1BlcmZUaW1lbGluZVN1cHBvcnRlZCwgaXNCcm93c2VyLCBpc1BlcmZUeXBlU3VwcG9ydGVkLCBpc0JlYWNvbkluc3BlY3Rpb25FbmFibGVkIH07IiwidmFyIF9leGNsdWRlZCA9IFtcInRhZ3NcIl07XG5cbmZ1bmN0aW9uIF9vYmplY3RXaXRob3V0UHJvcGVydGllc0xvb3NlKHNvdXJjZSwgZXhjbHVkZWQpIHsgaWYgKHNvdXJjZSA9PSBudWxsKSByZXR1cm4ge307IHZhciB0YXJnZXQgPSB7fTsgdmFyIHNvdXJjZUtleXMgPSBPYmplY3Qua2V5cyhzb3VyY2UpOyB2YXIga2V5LCBpOyBmb3IgKGkgPSAwOyBpIDwgc291cmNlS2V5cy5sZW5ndGg7IGkrKykgeyBrZXkgPSBzb3VyY2VLZXlzW2ldOyBpZiAoZXhjbHVkZWQuaW5kZXhPZihrZXkpID49IDApIGNvbnRpbnVlOyB0YXJnZXRba2V5XSA9IHNvdXJjZVtrZXldOyB9IHJldHVybiB0YXJnZXQ7IH1cblxuaW1wb3J0IHsgY3JlYXRlU3RhY2tUcmFjZXMsIGZpbHRlckludmFsaWRGcmFtZXMgfSBmcm9tICcuL3N0YWNrLXRyYWNlJztcbmltcG9ydCB7IGdlbmVyYXRlUmFuZG9tSWQsIG1lcmdlLCBleHRlbmQgfSBmcm9tICcuLi9jb21tb24vdXRpbHMnO1xuaW1wb3J0IHsgZ2V0UGFnZUNvbnRleHQgfSBmcm9tICcuLi9jb21tb24vY29udGV4dCc7XG5pbXBvcnQgeyB0cnVuY2F0ZU1vZGVsLCBFUlJPUl9NT0RFTCB9IGZyb20gJy4uL2NvbW1vbi90cnVuY2F0ZSc7XG5pbXBvcnQgc3RhY2tQYXJzZXIgZnJvbSAnZXJyb3Itc3RhY2stcGFyc2VyJztcbnZhciBJR05PUkVfS0VZUyA9IFsnc3RhY2snLCAnbWVzc2FnZSddO1xuXG5mdW5jdGlvbiBnZXRFcnJvclByb3BlcnRpZXMoZXJyb3IpIHtcbiAgdmFyIHByb3BlcnR5Rm91bmQgPSBmYWxzZTtcbiAgdmFyIHByb3BlcnRpZXMgPSB7fTtcbiAgT2JqZWN0LmtleXMoZXJyb3IpLmZvckVhY2goZnVuY3Rpb24gKGtleSkge1xuICAgIGlmIChJR05PUkVfS0VZUy5pbmRleE9mKGtleSkgPj0gMCkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIHZhciB2YWwgPSBlcnJvcltrZXldO1xuXG4gICAgaWYgKHZhbCA9PSBudWxsIHx8IHR5cGVvZiB2YWwgPT09ICdmdW5jdGlvbicpIHtcbiAgICAgIHJldHVybjtcbiAgICB9XG5cbiAgICBpZiAodHlwZW9mIHZhbCA9PT0gJ29iamVjdCcpIHtcbiAgICAgIGlmICh0eXBlb2YgdmFsLnRvSVNPU3RyaW5nICE9PSAnZnVuY3Rpb24nKSByZXR1cm47XG4gICAgICB2YWwgPSB2YWwudG9JU09TdHJpbmcoKTtcbiAgICB9XG5cbiAgICBwcm9wZXJ0aWVzW2tleV0gPSB2YWw7XG4gICAgcHJvcGVydHlGb3VuZCA9IHRydWU7XG4gIH0pO1xuXG4gIGlmIChwcm9wZXJ0eUZvdW5kKSB7XG4gICAgcmV0dXJuIHByb3BlcnRpZXM7XG4gIH1cbn1cblxudmFyIEVycm9yTG9nZ2luZyA9IGZ1bmN0aW9uICgpIHtcbiAgZnVuY3Rpb24gRXJyb3JMb2dnaW5nKGFwbVNlcnZlciwgY29uZmlnU2VydmljZSwgdHJhbnNhY3Rpb25TZXJ2aWNlKSB7XG4gICAgdGhpcy5fYXBtU2VydmVyID0gYXBtU2VydmVyO1xuICAgIHRoaXMuX2NvbmZpZ1NlcnZpY2UgPSBjb25maWdTZXJ2aWNlO1xuICAgIHRoaXMuX3RyYW5zYWN0aW9uU2VydmljZSA9IHRyYW5zYWN0aW9uU2VydmljZTtcbiAgfVxuXG4gIHZhciBfcHJvdG8gPSBFcnJvckxvZ2dpbmcucHJvdG90eXBlO1xuXG4gIF9wcm90by5jcmVhdGVFcnJvckRhdGFNb2RlbCA9IGZ1bmN0aW9uIGNyZWF0ZUVycm9yRGF0YU1vZGVsKGVycm9yRXZlbnQpIHtcbiAgICB2YXIgZnJhbWVzID0gY3JlYXRlU3RhY2tUcmFjZXMoc3RhY2tQYXJzZXIsIGVycm9yRXZlbnQpO1xuICAgIHZhciBmaWx0ZXJlZEZyYW1lcyA9IGZpbHRlckludmFsaWRGcmFtZXMoZnJhbWVzKTtcbiAgICB2YXIgY3VscHJpdCA9ICcoaW5saW5lIHNjcmlwdCknO1xuICAgIHZhciBsYXN0RnJhbWUgPSBmaWx0ZXJlZEZyYW1lc1tmaWx0ZXJlZEZyYW1lcy5sZW5ndGggLSAxXTtcblxuICAgIGlmIChsYXN0RnJhbWUgJiYgbGFzdEZyYW1lLmZpbGVuYW1lKSB7XG4gICAgICBjdWxwcml0ID0gbGFzdEZyYW1lLmZpbGVuYW1lO1xuICAgIH1cblxuICAgIHZhciBtZXNzYWdlID0gZXJyb3JFdmVudC5tZXNzYWdlLFxuICAgICAgICBlcnJvciA9IGVycm9yRXZlbnQuZXJyb3I7XG4gICAgdmFyIGVycm9yTWVzc2FnZSA9IG1lc3NhZ2U7XG4gICAgdmFyIGVycm9yVHlwZSA9ICcnO1xuICAgIHZhciBlcnJvckNvbnRleHQgPSB7fTtcblxuICAgIGlmIChlcnJvciAmJiB0eXBlb2YgZXJyb3IgPT09ICdvYmplY3QnKSB7XG4gICAgICBlcnJvck1lc3NhZ2UgPSBlcnJvck1lc3NhZ2UgfHwgZXJyb3IubWVzc2FnZTtcbiAgICAgIGVycm9yVHlwZSA9IGVycm9yLm5hbWU7XG4gICAgICB2YXIgY3VzdG9tUHJvcGVydGllcyA9IGdldEVycm9yUHJvcGVydGllcyhlcnJvcik7XG5cbiAgICAgIGlmIChjdXN0b21Qcm9wZXJ0aWVzKSB7XG4gICAgICAgIGVycm9yQ29udGV4dC5jdXN0b20gPSBjdXN0b21Qcm9wZXJ0aWVzO1xuICAgICAgfVxuICAgIH1cblxuICAgIGlmICghZXJyb3JUeXBlKSB7XG4gICAgICBpZiAoZXJyb3JNZXNzYWdlICYmIGVycm9yTWVzc2FnZS5pbmRleE9mKCc6JykgPiAtMSkge1xuICAgICAgICBlcnJvclR5cGUgPSBlcnJvck1lc3NhZ2Uuc3BsaXQoJzonKVswXTtcbiAgICAgIH1cbiAgICB9XG5cbiAgICB2YXIgY3VycmVudFRyYW5zYWN0aW9uID0gdGhpcy5fdHJhbnNhY3Rpb25TZXJ2aWNlLmdldEN1cnJlbnRUcmFuc2FjdGlvbigpO1xuXG4gICAgdmFyIHRyYW5zYWN0aW9uQ29udGV4dCA9IGN1cnJlbnRUcmFuc2FjdGlvbiA/IGN1cnJlbnRUcmFuc2FjdGlvbi5jb250ZXh0IDoge307XG5cbiAgICB2YXIgX3RoaXMkX2NvbmZpZ1NlcnZpY2UkID0gdGhpcy5fY29uZmlnU2VydmljZS5nZXQoJ2NvbnRleHQnKSxcbiAgICAgICAgdGFncyA9IF90aGlzJF9jb25maWdTZXJ2aWNlJC50YWdzLFxuICAgICAgICBjb25maWdDb250ZXh0ID0gX29iamVjdFdpdGhvdXRQcm9wZXJ0aWVzTG9vc2UoX3RoaXMkX2NvbmZpZ1NlcnZpY2UkLCBfZXhjbHVkZWQpO1xuXG4gICAgdmFyIHBhZ2VDb250ZXh0ID0gZ2V0UGFnZUNvbnRleHQoKTtcbiAgICB2YXIgY29udGV4dCA9IG1lcmdlKHt9LCBwYWdlQ29udGV4dCwgdHJhbnNhY3Rpb25Db250ZXh0LCBjb25maWdDb250ZXh0LCBlcnJvckNvbnRleHQpO1xuICAgIHZhciBlcnJvck9iamVjdCA9IHtcbiAgICAgIGlkOiBnZW5lcmF0ZVJhbmRvbUlkKCksXG4gICAgICBjdWxwcml0OiBjdWxwcml0LFxuICAgICAgZXhjZXB0aW9uOiB7XG4gICAgICAgIG1lc3NhZ2U6IGVycm9yTWVzc2FnZSxcbiAgICAgICAgc3RhY2t0cmFjZTogZmlsdGVyZWRGcmFtZXMsXG4gICAgICAgIHR5cGU6IGVycm9yVHlwZVxuICAgICAgfSxcbiAgICAgIGNvbnRleHQ6IGNvbnRleHRcbiAgICB9O1xuXG4gICAgaWYgKGN1cnJlbnRUcmFuc2FjdGlvbikge1xuICAgICAgZXJyb3JPYmplY3QgPSBleHRlbmQoZXJyb3JPYmplY3QsIHtcbiAgICAgICAgdHJhY2VfaWQ6IGN1cnJlbnRUcmFuc2FjdGlvbi50cmFjZUlkLFxuICAgICAgICBwYXJlbnRfaWQ6IGN1cnJlbnRUcmFuc2FjdGlvbi5pZCxcbiAgICAgICAgdHJhbnNhY3Rpb25faWQ6IGN1cnJlbnRUcmFuc2FjdGlvbi5pZCxcbiAgICAgICAgdHJhbnNhY3Rpb246IHtcbiAgICAgICAgICB0eXBlOiBjdXJyZW50VHJhbnNhY3Rpb24udHlwZSxcbiAgICAgICAgICBzYW1wbGVkOiBjdXJyZW50VHJhbnNhY3Rpb24uc2FtcGxlZFxuICAgICAgICB9XG4gICAgICB9KTtcbiAgICB9XG5cbiAgICByZXR1cm4gdHJ1bmNhdGVNb2RlbChFUlJPUl9NT0RFTCwgZXJyb3JPYmplY3QpO1xuICB9O1xuXG4gIF9wcm90by5sb2dFcnJvckV2ZW50ID0gZnVuY3Rpb24gbG9nRXJyb3JFdmVudChlcnJvckV2ZW50KSB7XG4gICAgaWYgKHR5cGVvZiBlcnJvckV2ZW50ID09PSAndW5kZWZpbmVkJykge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIHZhciBlcnJvck9iamVjdCA9IHRoaXMuY3JlYXRlRXJyb3JEYXRhTW9kZWwoZXJyb3JFdmVudCk7XG5cbiAgICBpZiAodHlwZW9mIGVycm9yT2JqZWN0LmV4Y2VwdGlvbi5tZXNzYWdlID09PSAndW5kZWZpbmVkJykge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIHRoaXMuX2FwbVNlcnZlci5hZGRFcnJvcihlcnJvck9iamVjdCk7XG4gIH07XG5cbiAgX3Byb3RvLnJlZ2lzdGVyTGlzdGVuZXJzID0gZnVuY3Rpb24gcmVnaXN0ZXJMaXN0ZW5lcnMoKSB7XG4gICAgdmFyIF90aGlzID0gdGhpcztcblxuICAgIHdpbmRvdy5hZGRFdmVudExpc3RlbmVyKCdlcnJvcicsIGZ1bmN0aW9uIChlcnJvckV2ZW50KSB7XG4gICAgICByZXR1cm4gX3RoaXMubG9nRXJyb3JFdmVudChlcnJvckV2ZW50KTtcbiAgICB9KTtcbiAgICB3aW5kb3cuYWRkRXZlbnRMaXN0ZW5lcigndW5oYW5kbGVkcmVqZWN0aW9uJywgZnVuY3Rpb24gKHByb21pc2VSZWplY3Rpb25FdmVudCkge1xuICAgICAgcmV0dXJuIF90aGlzLmxvZ1Byb21pc2VFdmVudChwcm9taXNlUmVqZWN0aW9uRXZlbnQpO1xuICAgIH0pO1xuICB9O1xuXG4gIF9wcm90by5sb2dQcm9taXNlRXZlbnQgPSBmdW5jdGlvbiBsb2dQcm9taXNlRXZlbnQocHJvbWlzZVJlamVjdGlvbkV2ZW50KSB7XG4gICAgdmFyIHByZWZpeCA9ICdVbmhhbmRsZWQgcHJvbWlzZSByZWplY3Rpb246ICc7XG4gICAgdmFyIHJlYXNvbiA9IHByb21pc2VSZWplY3Rpb25FdmVudC5yZWFzb247XG5cbiAgICBpZiAocmVhc29uID09IG51bGwpIHtcbiAgICAgIHJlYXNvbiA9ICc8bm8gcmVhc29uIHNwZWNpZmllZD4nO1xuICAgIH1cblxuICAgIHZhciBlcnJvckV2ZW50O1xuXG4gICAgaWYgKHR5cGVvZiByZWFzb24ubWVzc2FnZSA9PT0gJ3N0cmluZycpIHtcbiAgICAgIHZhciBuYW1lID0gcmVhc29uLm5hbWUgPyByZWFzb24ubmFtZSArICc6ICcgOiAnJztcbiAgICAgIGVycm9yRXZlbnQgPSB7XG4gICAgICAgIGVycm9yOiByZWFzb24sXG4gICAgICAgIG1lc3NhZ2U6IHByZWZpeCArIG5hbWUgKyByZWFzb24ubWVzc2FnZVxuICAgICAgfTtcbiAgICB9IGVsc2Uge1xuICAgICAgcmVhc29uID0gdHlwZW9mIHJlYXNvbiA9PT0gJ29iamVjdCcgPyAnPG9iamVjdD4nIDogdHlwZW9mIHJlYXNvbiA9PT0gJ2Z1bmN0aW9uJyA/ICc8ZnVuY3Rpb24+JyA6IHJlYXNvbjtcbiAgICAgIGVycm9yRXZlbnQgPSB7XG4gICAgICAgIG1lc3NhZ2U6IHByZWZpeCArIHJlYXNvblxuICAgICAgfTtcbiAgICB9XG5cbiAgICB0aGlzLmxvZ0Vycm9yRXZlbnQoZXJyb3JFdmVudCk7XG4gIH07XG5cbiAgX3Byb3RvLmxvZ0Vycm9yID0gZnVuY3Rpb24gbG9nRXJyb3IobWVzc2FnZU9yRXJyb3IpIHtcbiAgICB2YXIgZXJyb3JFdmVudCA9IHt9O1xuXG4gICAgaWYgKHR5cGVvZiBtZXNzYWdlT3JFcnJvciA9PT0gJ3N0cmluZycpIHtcbiAgICAgIGVycm9yRXZlbnQubWVzc2FnZSA9IG1lc3NhZ2VPckVycm9yO1xuICAgIH0gZWxzZSB7XG4gICAgICBlcnJvckV2ZW50LmVycm9yID0gbWVzc2FnZU9yRXJyb3I7XG4gICAgfVxuXG4gICAgcmV0dXJuIHRoaXMubG9nRXJyb3JFdmVudChlcnJvckV2ZW50KTtcbiAgfTtcblxuICByZXR1cm4gRXJyb3JMb2dnaW5nO1xufSgpO1xuXG5leHBvcnQgZGVmYXVsdCBFcnJvckxvZ2dpbmc7IiwiaW1wb3J0IEVycm9yTG9nZ2luZyBmcm9tICcuL2Vycm9yLWxvZ2dpbmcnO1xuaW1wb3J0IHsgQ09ORklHX1NFUlZJQ0UsIFRSQU5TQUNUSU9OX1NFUlZJQ0UsIEVSUk9SX0xPR0dJTkcsIEFQTV9TRVJWRVIgfSBmcm9tICcuLi9jb21tb24vY29uc3RhbnRzJztcbmltcG9ydCB7IHNlcnZpY2VDcmVhdG9ycyB9IGZyb20gJy4uL2NvbW1vbi9zZXJ2aWNlLWZhY3RvcnknO1xuXG5mdW5jdGlvbiByZWdpc3RlclNlcnZpY2VzKCkge1xuICBzZXJ2aWNlQ3JlYXRvcnNbRVJST1JfTE9HR0lOR10gPSBmdW5jdGlvbiAoc2VydmljZUZhY3RvcnkpIHtcbiAgICB2YXIgX3NlcnZpY2VGYWN0b3J5JGdldFNlID0gc2VydmljZUZhY3RvcnkuZ2V0U2VydmljZShbQVBNX1NFUlZFUiwgQ09ORklHX1NFUlZJQ0UsIFRSQU5TQUNUSU9OX1NFUlZJQ0VdKSxcbiAgICAgICAgYXBtU2VydmVyID0gX3NlcnZpY2VGYWN0b3J5JGdldFNlWzBdLFxuICAgICAgICBjb25maWdTZXJ2aWNlID0gX3NlcnZpY2VGYWN0b3J5JGdldFNlWzFdLFxuICAgICAgICB0cmFuc2FjdGlvblNlcnZpY2UgPSBfc2VydmljZUZhY3RvcnkkZ2V0U2VbMl07XG5cbiAgICByZXR1cm4gbmV3IEVycm9yTG9nZ2luZyhhcG1TZXJ2ZXIsIGNvbmZpZ1NlcnZpY2UsIHRyYW5zYWN0aW9uU2VydmljZSk7XG4gIH07XG59XG5cbmV4cG9ydCB7IHJlZ2lzdGVyU2VydmljZXMgfTsiLCJmdW5jdGlvbiBmaWxlUGF0aFRvRmlsZU5hbWUoZmlsZVVybCkge1xuICB2YXIgb3JpZ2luID0gd2luZG93LmxvY2F0aW9uLm9yaWdpbiB8fCB3aW5kb3cubG9jYXRpb24ucHJvdG9jb2wgKyAnLy8nICsgd2luZG93LmxvY2F0aW9uLmhvc3RuYW1lICsgKHdpbmRvdy5sb2NhdGlvbi5wb3J0ID8gJzonICsgd2luZG93LmxvY2F0aW9uLnBvcnQgOiAnJyk7XG5cbiAgaWYgKGZpbGVVcmwuaW5kZXhPZihvcmlnaW4pID4gLTEpIHtcbiAgICBmaWxlVXJsID0gZmlsZVVybC5yZXBsYWNlKG9yaWdpbiArICcvJywgJycpO1xuICB9XG5cbiAgcmV0dXJuIGZpbGVVcmw7XG59XG5cbmZ1bmN0aW9uIGNsZWFuRmlsZVBhdGgoZmlsZVBhdGgpIHtcbiAgaWYgKGZpbGVQYXRoID09PSB2b2lkIDApIHtcbiAgICBmaWxlUGF0aCA9ICcnO1xuICB9XG5cbiAgaWYgKGZpbGVQYXRoID09PSAnPGFub255bW91cz4nKSB7XG4gICAgZmlsZVBhdGggPSAnJztcbiAgfVxuXG4gIHJldHVybiBmaWxlUGF0aDtcbn1cblxuZnVuY3Rpb24gaXNGaWxlSW5saW5lKGZpbGVVcmwpIHtcbiAgaWYgKGZpbGVVcmwpIHtcbiAgICByZXR1cm4gd2luZG93LmxvY2F0aW9uLmhyZWYuaW5kZXhPZihmaWxlVXJsKSA9PT0gMDtcbiAgfVxuXG4gIHJldHVybiBmYWxzZTtcbn1cblxuZnVuY3Rpb24gbm9ybWFsaXplU3RhY2tGcmFtZXMoc3RhY2tGcmFtZXMpIHtcbiAgcmV0dXJuIHN0YWNrRnJhbWVzLm1hcChmdW5jdGlvbiAoZnJhbWUpIHtcbiAgICBpZiAoZnJhbWUuZnVuY3Rpb25OYW1lKSB7XG4gICAgICBmcmFtZS5mdW5jdGlvbk5hbWUgPSBub3JtYWxpemVGdW5jdGlvbk5hbWUoZnJhbWUuZnVuY3Rpb25OYW1lKTtcbiAgICB9XG5cbiAgICByZXR1cm4gZnJhbWU7XG4gIH0pO1xufVxuXG5mdW5jdGlvbiBub3JtYWxpemVGdW5jdGlvbk5hbWUoZm5OYW1lKSB7XG4gIHZhciBwYXJ0cyA9IGZuTmFtZS5zcGxpdCgnLycpO1xuXG4gIGlmIChwYXJ0cy5sZW5ndGggPiAxKSB7XG4gICAgZm5OYW1lID0gWydPYmplY3QnLCBwYXJ0c1twYXJ0cy5sZW5ndGggLSAxXV0uam9pbignLicpO1xuICB9IGVsc2Uge1xuICAgIGZuTmFtZSA9IHBhcnRzWzBdO1xuICB9XG5cbiAgZm5OYW1lID0gZm5OYW1lLnJlcGxhY2UoLy48JC9naSwgJy48YW5vbnltb3VzPicpO1xuICBmbk5hbWUgPSBmbk5hbWUucmVwbGFjZSgvXkFub255bW91cyBmdW5jdGlvbiQvLCAnPGFub255bW91cz4nKTtcbiAgcGFydHMgPSBmbk5hbWUuc3BsaXQoJy4nKTtcblxuICBpZiAocGFydHMubGVuZ3RoID4gMSkge1xuICAgIGZuTmFtZSA9IHBhcnRzW3BhcnRzLmxlbmd0aCAtIDFdO1xuICB9IGVsc2Uge1xuICAgIGZuTmFtZSA9IHBhcnRzWzBdO1xuICB9XG5cbiAgcmV0dXJuIGZuTmFtZTtcbn1cblxuZnVuY3Rpb24gaXNWYWxpZFN0YWNrVHJhY2Uoc3RhY2tUcmFjZXMpIHtcbiAgaWYgKHN0YWNrVHJhY2VzLmxlbmd0aCA9PT0gMCkge1xuICAgIHJldHVybiBmYWxzZTtcbiAgfVxuXG4gIGlmIChzdGFja1RyYWNlcy5sZW5ndGggPT09IDEpIHtcbiAgICB2YXIgc3RhY2tUcmFjZSA9IHN0YWNrVHJhY2VzWzBdO1xuICAgIHJldHVybiAnbGluZU51bWJlcicgaW4gc3RhY2tUcmFjZTtcbiAgfVxuXG4gIHJldHVybiB0cnVlO1xufVxuXG5leHBvcnQgZnVuY3Rpb24gY3JlYXRlU3RhY2tUcmFjZXMoc3RhY2tQYXJzZXIsIGVycm9yRXZlbnQpIHtcbiAgdmFyIGVycm9yID0gZXJyb3JFdmVudC5lcnJvcixcbiAgICAgIGZpbGVuYW1lID0gZXJyb3JFdmVudC5maWxlbmFtZSxcbiAgICAgIGxpbmVubyA9IGVycm9yRXZlbnQubGluZW5vLFxuICAgICAgY29sbm8gPSBlcnJvckV2ZW50LmNvbG5vO1xuICB2YXIgc3RhY2tUcmFjZXMgPSBbXTtcblxuICBpZiAoZXJyb3IpIHtcbiAgICB0cnkge1xuICAgICAgc3RhY2tUcmFjZXMgPSBzdGFja1BhcnNlci5wYXJzZShlcnJvcik7XG4gICAgfSBjYXRjaCAoZSkge31cbiAgfVxuXG4gIGlmICghaXNWYWxpZFN0YWNrVHJhY2Uoc3RhY2tUcmFjZXMpKSB7XG4gICAgc3RhY2tUcmFjZXMgPSBbe1xuICAgICAgZmlsZU5hbWU6IGZpbGVuYW1lLFxuICAgICAgbGluZU51bWJlcjogbGluZW5vLFxuICAgICAgY29sdW1uTnVtYmVyOiBjb2xub1xuICAgIH1dO1xuICB9XG5cbiAgdmFyIG5vcm1hbGl6ZWRTdGFja1RyYWNlcyA9IG5vcm1hbGl6ZVN0YWNrRnJhbWVzKHN0YWNrVHJhY2VzKTtcbiAgcmV0dXJuIG5vcm1hbGl6ZWRTdGFja1RyYWNlcy5tYXAoZnVuY3Rpb24gKHN0YWNrKSB7XG4gICAgdmFyIGZpbGVOYW1lID0gc3RhY2suZmlsZU5hbWUsXG4gICAgICAgIGxpbmVOdW1iZXIgPSBzdGFjay5saW5lTnVtYmVyLFxuICAgICAgICBjb2x1bW5OdW1iZXIgPSBzdGFjay5jb2x1bW5OdW1iZXIsXG4gICAgICAgIF9zdGFjayRmdW5jdGlvbk5hbWUgPSBzdGFjay5mdW5jdGlvbk5hbWUsXG4gICAgICAgIGZ1bmN0aW9uTmFtZSA9IF9zdGFjayRmdW5jdGlvbk5hbWUgPT09IHZvaWQgMCA/ICc8YW5vbnltb3VzPicgOiBfc3RhY2skZnVuY3Rpb25OYW1lO1xuXG4gICAgaWYgKCFmaWxlTmFtZSAmJiAhbGluZU51bWJlcikge1xuICAgICAgcmV0dXJuIHt9O1xuICAgIH1cblxuICAgIGlmICghY29sdW1uTnVtYmVyICYmICFsaW5lTnVtYmVyKSB7XG4gICAgICByZXR1cm4ge307XG4gICAgfVxuXG4gICAgdmFyIGZpbGVQYXRoID0gY2xlYW5GaWxlUGF0aChmaWxlTmFtZSk7XG4gICAgdmFyIGNsZWFuZWRGaWxlTmFtZSA9IGZpbGVQYXRoVG9GaWxlTmFtZShmaWxlUGF0aCk7XG5cbiAgICBpZiAoaXNGaWxlSW5saW5lKGZpbGVQYXRoKSkge1xuICAgICAgY2xlYW5lZEZpbGVOYW1lID0gJyhpbmxpbmUgc2NyaXB0KSc7XG4gICAgfVxuXG4gICAgcmV0dXJuIHtcbiAgICAgIGFic19wYXRoOiBmaWxlTmFtZSxcbiAgICAgIGZpbGVuYW1lOiBjbGVhbmVkRmlsZU5hbWUsXG4gICAgICBmdW5jdGlvbjogZnVuY3Rpb25OYW1lLFxuICAgICAgbGluZW5vOiBsaW5lTnVtYmVyLFxuICAgICAgY29sbm86IGNvbHVtbk51bWJlclxuICAgIH07XG4gIH0pO1xufVxuZXhwb3J0IGZ1bmN0aW9uIGZpbHRlckludmFsaWRGcmFtZXMoZnJhbWVzKSB7XG4gIHJldHVybiBmcmFtZXMuZmlsdGVyKGZ1bmN0aW9uIChfcmVmKSB7XG4gICAgdmFyIGZpbGVuYW1lID0gX3JlZi5maWxlbmFtZSxcbiAgICAgICAgbGluZW5vID0gX3JlZi5saW5lbm87XG4gICAgcmV0dXJuIHR5cGVvZiBmaWxlbmFtZSAhPT0gJ3VuZGVmaW5lZCcgJiYgdHlwZW9mIGxpbmVubyAhPT0gJ3VuZGVmaW5lZCc7XG4gIH0pO1xufSIsImltcG9ydCB7IHJlZ2lzdGVyU2VydmljZXMgYXMgcmVnaXN0ZXJFcnJvclNlcnZpY2VzIH0gZnJvbSAnLi9lcnJvci1sb2dnaW5nJztcbmltcG9ydCB7IHJlZ2lzdGVyU2VydmljZXMgYXMgcmVnaXN0ZXJQZXJmU2VydmljZXMgfSBmcm9tICcuL3BlcmZvcm1hbmNlLW1vbml0b3JpbmcnO1xuaW1wb3J0IHsgU2VydmljZUZhY3RvcnkgfSBmcm9tICcuL2NvbW1vbi9zZXJ2aWNlLWZhY3RvcnknO1xuaW1wb3J0IHsgaXNQbGF0Zm9ybVN1cHBvcnRlZCwgc2NoZWR1bGVNaWNyb1Rhc2ssIHNjaGVkdWxlTWFjcm9UYXNrLCBpc0Jyb3dzZXIgfSBmcm9tICcuL2NvbW1vbi91dGlscyc7XG5pbXBvcnQgeyBwYXRjaEFsbCwgcGF0Y2hFdmVudEhhbmRsZXIgfSBmcm9tICcuL2NvbW1vbi9wYXRjaGluZyc7XG5pbXBvcnQgeyBvYnNlcnZlUGFnZVZpc2liaWxpdHksIG9ic2VydmVQYWdlQ2xpY2tzIH0gZnJvbSAnLi9jb21tb24vb2JzZXJ2ZXJzJztcbmltcG9ydCB7IFBBR0VfTE9BRF9ERUxBWSwgUEFHRV9MT0FELCBFUlJPUiwgQ09ORklHX1NFUlZJQ0UsIExPR0dJTkdfU0VSVklDRSwgVFJBTlNBQ1RJT05fU0VSVklDRSwgQVBNX1NFUlZFUiwgUEVSRk9STUFOQ0VfTU9OSVRPUklORywgRVJST1JfTE9HR0lORywgRVZFTlRfVEFSR0VULCBDTElDSyB9IGZyb20gJy4vY29tbW9uL2NvbnN0YW50cyc7XG5pbXBvcnQgeyBnZXRJbnN0cnVtZW50YXRpb25GbGFncyB9IGZyb20gJy4vY29tbW9uL2luc3RydW1lbnQnO1xuaW1wb3J0IGFmdGVyRnJhbWUgZnJvbSAnLi9jb21tb24vYWZ0ZXItZnJhbWUnO1xuaW1wb3J0IHsgYm9vdHN0cmFwIH0gZnJvbSAnLi9ib290c3RyYXAnO1xuaW1wb3J0IHsgY3JlYXRlVHJhY2VyIH0gZnJvbSAnLi9vcGVudHJhY2luZyc7XG5cbmZ1bmN0aW9uIGNyZWF0ZVNlcnZpY2VGYWN0b3J5KCkge1xuICByZWdpc3RlclBlcmZTZXJ2aWNlcygpO1xuICByZWdpc3RlckVycm9yU2VydmljZXMoKTtcbiAgdmFyIHNlcnZpY2VGYWN0b3J5ID0gbmV3IFNlcnZpY2VGYWN0b3J5KCk7XG4gIHJldHVybiBzZXJ2aWNlRmFjdG9yeTtcbn1cblxuZXhwb3J0IHsgY3JlYXRlU2VydmljZUZhY3RvcnksIFNlcnZpY2VGYWN0b3J5LCBwYXRjaEFsbCwgcGF0Y2hFdmVudEhhbmRsZXIsIGlzUGxhdGZvcm1TdXBwb3J0ZWQsIGlzQnJvd3NlciwgZ2V0SW5zdHJ1bWVudGF0aW9uRmxhZ3MsIGNyZWF0ZVRyYWNlciwgc2NoZWR1bGVNaWNyb1Rhc2ssIHNjaGVkdWxlTWFjcm9UYXNrLCBhZnRlckZyYW1lLCBFUlJPUiwgUEFHRV9MT0FEX0RFTEFZLCBQQUdFX0xPQUQsIENPTkZJR19TRVJWSUNFLCBMT0dHSU5HX1NFUlZJQ0UsIFRSQU5TQUNUSU9OX1NFUlZJQ0UsIEFQTV9TRVJWRVIsIFBFUkZPUk1BTkNFX01PTklUT1JJTkcsIEVSUk9SX0xPR0dJTkcsIEVWRU5UX1RBUkdFVCwgQ0xJQ0ssIGJvb3RzdHJhcCwgb2JzZXJ2ZVBhZ2VWaXNpYmlsaXR5LCBvYnNlcnZlUGFnZUNsaWNrcyB9OyIsImltcG9ydCBUcmFjZXIgZnJvbSAnLi90cmFjZXInO1xuaW1wb3J0IFNwYW4gZnJvbSAnLi9zcGFuJztcbmltcG9ydCB7IFRSQU5TQUNUSU9OX1NFUlZJQ0UsIExPR0dJTkdfU0VSVklDRSwgUEVSRk9STUFOQ0VfTU9OSVRPUklORywgRVJST1JfTE9HR0lORyB9IGZyb20gJy4uL2NvbW1vbi9jb25zdGFudHMnO1xuXG5mdW5jdGlvbiBjcmVhdGVUcmFjZXIoc2VydmljZUZhY3RvcnkpIHtcbiAgdmFyIHBlcmZvcm1hbmNlTW9uaXRvcmluZyA9IHNlcnZpY2VGYWN0b3J5LmdldFNlcnZpY2UoUEVSRk9STUFOQ0VfTU9OSVRPUklORyk7XG4gIHZhciB0cmFuc2FjdGlvblNlcnZpY2UgPSBzZXJ2aWNlRmFjdG9yeS5nZXRTZXJ2aWNlKFRSQU5TQUNUSU9OX1NFUlZJQ0UpO1xuICB2YXIgZXJyb3JMb2dnaW5nID0gc2VydmljZUZhY3RvcnkuZ2V0U2VydmljZShFUlJPUl9MT0dHSU5HKTtcbiAgdmFyIGxvZ2dpbmdTZXJ2aWNlID0gc2VydmljZUZhY3RvcnkuZ2V0U2VydmljZShMT0dHSU5HX1NFUlZJQ0UpO1xuICByZXR1cm4gbmV3IFRyYWNlcihwZXJmb3JtYW5jZU1vbml0b3JpbmcsIHRyYW5zYWN0aW9uU2VydmljZSwgbG9nZ2luZ1NlcnZpY2UsIGVycm9yTG9nZ2luZyk7XG59XG5cbmV4cG9ydCB7IFNwYW4sIFRyYWNlciwgY3JlYXRlVHJhY2VyIH07IiwiZnVuY3Rpb24gX2luaGVyaXRzTG9vc2Uoc3ViQ2xhc3MsIHN1cGVyQ2xhc3MpIHsgc3ViQ2xhc3MucHJvdG90eXBlID0gT2JqZWN0LmNyZWF0ZShzdXBlckNsYXNzLnByb3RvdHlwZSk7IHN1YkNsYXNzLnByb3RvdHlwZS5jb25zdHJ1Y3RvciA9IHN1YkNsYXNzOyBfc2V0UHJvdG90eXBlT2Yoc3ViQ2xhc3MsIHN1cGVyQ2xhc3MpOyB9XG5cbmZ1bmN0aW9uIF9zZXRQcm90b3R5cGVPZihvLCBwKSB7IF9zZXRQcm90b3R5cGVPZiA9IE9iamVjdC5zZXRQcm90b3R5cGVPZiB8fCBmdW5jdGlvbiBfc2V0UHJvdG90eXBlT2YobywgcCkgeyBvLl9fcHJvdG9fXyA9IHA7IHJldHVybiBvOyB9OyByZXR1cm4gX3NldFByb3RvdHlwZU9mKG8sIHApOyB9XG5cbmltcG9ydCB7IFNwYW4gYXMgb3RTcGFuIH0gZnJvbSAnb3BlbnRyYWNpbmcvbGliL3NwYW4nO1xuaW1wb3J0IHsgZXh0ZW5kLCBnZXRUaW1lT3JpZ2luIH0gZnJvbSAnLi4vY29tbW9uL3V0aWxzJztcbmltcG9ydCBUcmFuc2FjdGlvbiBmcm9tICcuLi9wZXJmb3JtYW5jZS1tb25pdG9yaW5nL3RyYW5zYWN0aW9uJztcblxudmFyIFNwYW4gPSBmdW5jdGlvbiAoX290U3Bhbikge1xuICBfaW5oZXJpdHNMb29zZShTcGFuLCBfb3RTcGFuKTtcblxuICBmdW5jdGlvbiBTcGFuKHRyYWNlciwgc3Bhbikge1xuICAgIHZhciBfdGhpcztcblxuICAgIF90aGlzID0gX290U3Bhbi5jYWxsKHRoaXMpIHx8IHRoaXM7XG4gICAgX3RoaXMuX190cmFjZXIgPSB0cmFjZXI7XG4gICAgX3RoaXMuc3BhbiA9IHNwYW47XG4gICAgX3RoaXMuaXNUcmFuc2FjdGlvbiA9IHNwYW4gaW5zdGFuY2VvZiBUcmFuc2FjdGlvbjtcbiAgICBfdGhpcy5zcGFuQ29udGV4dCA9IHtcbiAgICAgIGlkOiBzcGFuLmlkLFxuICAgICAgdHJhY2VJZDogc3Bhbi50cmFjZUlkLFxuICAgICAgc2FtcGxlZDogc3Bhbi5zYW1wbGVkXG4gICAgfTtcbiAgICByZXR1cm4gX3RoaXM7XG4gIH1cblxuICB2YXIgX3Byb3RvID0gU3Bhbi5wcm90b3R5cGU7XG5cbiAgX3Byb3RvLl9jb250ZXh0ID0gZnVuY3Rpb24gX2NvbnRleHQoKSB7XG4gICAgcmV0dXJuIHRoaXMuc3BhbkNvbnRleHQ7XG4gIH07XG5cbiAgX3Byb3RvLl90cmFjZXIgPSBmdW5jdGlvbiBfdHJhY2VyKCkge1xuICAgIHJldHVybiB0aGlzLl9fdHJhY2VyO1xuICB9O1xuXG4gIF9wcm90by5fc2V0T3BlcmF0aW9uTmFtZSA9IGZ1bmN0aW9uIF9zZXRPcGVyYXRpb25OYW1lKG5hbWUpIHtcbiAgICB0aGlzLnNwYW4ubmFtZSA9IG5hbWU7XG4gIH07XG5cbiAgX3Byb3RvLl9hZGRUYWdzID0gZnVuY3Rpb24gX2FkZFRhZ3Moa2V5VmFsdWVQYWlycykge1xuICAgIHZhciB0YWdzID0gZXh0ZW5kKHt9LCBrZXlWYWx1ZVBhaXJzKTtcblxuICAgIGlmICh0YWdzLnR5cGUpIHtcbiAgICAgIHRoaXMuc3Bhbi50eXBlID0gdGFncy50eXBlO1xuICAgICAgZGVsZXRlIHRhZ3MudHlwZTtcbiAgICB9XG5cbiAgICBpZiAodGhpcy5pc1RyYW5zYWN0aW9uKSB7XG4gICAgICB2YXIgdXNlcklkID0gdGFnc1sndXNlci5pZCddO1xuICAgICAgdmFyIHVzZXJuYW1lID0gdGFnc1sndXNlci51c2VybmFtZSddO1xuICAgICAgdmFyIGVtYWlsID0gdGFnc1sndXNlci5lbWFpbCddO1xuXG4gICAgICBpZiAodXNlcklkIHx8IHVzZXJuYW1lIHx8IGVtYWlsKSB7XG4gICAgICAgIHRoaXMuc3Bhbi5hZGRDb250ZXh0KHtcbiAgICAgICAgICB1c2VyOiB7XG4gICAgICAgICAgICBpZDogdXNlcklkLFxuICAgICAgICAgICAgdXNlcm5hbWU6IHVzZXJuYW1lLFxuICAgICAgICAgICAgZW1haWw6IGVtYWlsXG4gICAgICAgICAgfVxuICAgICAgICB9KTtcbiAgICAgICAgZGVsZXRlIHRhZ3NbJ3VzZXIuaWQnXTtcbiAgICAgICAgZGVsZXRlIHRhZ3NbJ3VzZXIudXNlcm5hbWUnXTtcbiAgICAgICAgZGVsZXRlIHRhZ3NbJ3VzZXIuZW1haWwnXTtcbiAgICAgIH1cbiAgICB9XG5cbiAgICB0aGlzLnNwYW4uYWRkTGFiZWxzKHRhZ3MpO1xuICB9O1xuXG4gIF9wcm90by5fbG9nID0gZnVuY3Rpb24gX2xvZyhsb2csIHRpbWVzdGFtcCkge1xuICAgIGlmIChsb2cuZXZlbnQgPT09ICdlcnJvcicpIHtcbiAgICAgIGlmIChsb2dbJ2Vycm9yLm9iamVjdCddKSB7XG4gICAgICAgIHRoaXMuX190cmFjZXIuZXJyb3JMb2dnaW5nLmxvZ0Vycm9yKGxvZ1snZXJyb3Iub2JqZWN0J10pO1xuICAgICAgfSBlbHNlIGlmIChsb2cubWVzc2FnZSkge1xuICAgICAgICB0aGlzLl9fdHJhY2VyLmVycm9yTG9nZ2luZy5sb2dFcnJvcihsb2cubWVzc2FnZSk7XG4gICAgICB9XG4gICAgfVxuICB9O1xuXG4gIF9wcm90by5fZmluaXNoID0gZnVuY3Rpb24gX2ZpbmlzaChmaW5pc2hUaW1lKSB7XG4gICAgdGhpcy5zcGFuLmVuZCgpO1xuXG4gICAgaWYgKGZpbmlzaFRpbWUpIHtcbiAgICAgIHRoaXMuc3Bhbi5fZW5kID0gZmluaXNoVGltZSAtIGdldFRpbWVPcmlnaW4oKTtcbiAgICB9XG4gIH07XG5cbiAgcmV0dXJuIFNwYW47XG59KG90U3Bhbik7XG5cbmV4cG9ydCBkZWZhdWx0IFNwYW47IiwiZnVuY3Rpb24gX2luaGVyaXRzTG9vc2Uoc3ViQ2xhc3MsIHN1cGVyQ2xhc3MpIHsgc3ViQ2xhc3MucHJvdG90eXBlID0gT2JqZWN0LmNyZWF0ZShzdXBlckNsYXNzLnByb3RvdHlwZSk7IHN1YkNsYXNzLnByb3RvdHlwZS5jb25zdHJ1Y3RvciA9IHN1YkNsYXNzOyBfc2V0UHJvdG90eXBlT2Yoc3ViQ2xhc3MsIHN1cGVyQ2xhc3MpOyB9XG5cbmZ1bmN0aW9uIF9zZXRQcm90b3R5cGVPZihvLCBwKSB7IF9zZXRQcm90b3R5cGVPZiA9IE9iamVjdC5zZXRQcm90b3R5cGVPZiB8fCBmdW5jdGlvbiBfc2V0UHJvdG90eXBlT2YobywgcCkgeyBvLl9fcHJvdG9fXyA9IHA7IHJldHVybiBvOyB9OyByZXR1cm4gX3NldFByb3RvdHlwZU9mKG8sIHApOyB9XG5cbmltcG9ydCB7IFRyYWNlciBhcyBvdFRyYWNlciB9IGZyb20gJ29wZW50cmFjaW5nL2xpYi90cmFjZXInO1xuaW1wb3J0IHsgUkVGRVJFTkNFX0NISUxEX09GLCBGT1JNQVRfVEVYVF9NQVAsIEZPUk1BVF9IVFRQX0hFQURFUlMsIEZPUk1BVF9CSU5BUlkgfSBmcm9tICdvcGVudHJhY2luZy9saWIvY29uc3RhbnRzJztcbmltcG9ydCB7IFNwYW4gYXMgTm9vcFNwYW4gfSBmcm9tICdvcGVudHJhY2luZy9saWIvc3Bhbic7XG5pbXBvcnQgeyBnZXRUaW1lT3JpZ2luLCBmaW5kIH0gZnJvbSAnLi4vY29tbW9uL3V0aWxzJztcbmltcG9ydCB7IF9fREVWX18gfSBmcm9tICcuLi9zdGF0ZSc7XG5pbXBvcnQgU3BhbiBmcm9tICcuL3NwYW4nO1xuXG52YXIgVHJhY2VyID0gZnVuY3Rpb24gKF9vdFRyYWNlcikge1xuICBfaW5oZXJpdHNMb29zZShUcmFjZXIsIF9vdFRyYWNlcik7XG5cbiAgZnVuY3Rpb24gVHJhY2VyKHBlcmZvcm1hbmNlTW9uaXRvcmluZywgdHJhbnNhY3Rpb25TZXJ2aWNlLCBsb2dnaW5nU2VydmljZSwgZXJyb3JMb2dnaW5nKSB7XG4gICAgdmFyIF90aGlzO1xuXG4gICAgX3RoaXMgPSBfb3RUcmFjZXIuY2FsbCh0aGlzKSB8fCB0aGlzO1xuICAgIF90aGlzLnBlcmZvcm1hbmNlTW9uaXRvcmluZyA9IHBlcmZvcm1hbmNlTW9uaXRvcmluZztcbiAgICBfdGhpcy50cmFuc2FjdGlvblNlcnZpY2UgPSB0cmFuc2FjdGlvblNlcnZpY2U7XG4gICAgX3RoaXMubG9nZ2luZ1NlcnZpY2UgPSBsb2dnaW5nU2VydmljZTtcbiAgICBfdGhpcy5lcnJvckxvZ2dpbmcgPSBlcnJvckxvZ2dpbmc7XG4gICAgcmV0dXJuIF90aGlzO1xuICB9XG5cbiAgdmFyIF9wcm90byA9IFRyYWNlci5wcm90b3R5cGU7XG5cbiAgX3Byb3RvLl9zdGFydFNwYW4gPSBmdW5jdGlvbiBfc3RhcnRTcGFuKG5hbWUsIG9wdGlvbnMpIHtcbiAgICB2YXIgc3Bhbk9wdGlvbnMgPSB7XG4gICAgICBtYW5hZ2VkOiB0cnVlXG4gICAgfTtcblxuICAgIGlmIChvcHRpb25zKSB7XG4gICAgICBzcGFuT3B0aW9ucy50aW1lc3RhbXAgPSBvcHRpb25zLnN0YXJ0VGltZTtcblxuICAgICAgaWYgKG9wdGlvbnMuY2hpbGRPZikge1xuICAgICAgICBzcGFuT3B0aW9ucy5wYXJlbnRJZCA9IG9wdGlvbnMuY2hpbGRPZi5pZDtcbiAgICAgIH0gZWxzZSBpZiAob3B0aW9ucy5yZWZlcmVuY2VzICYmIG9wdGlvbnMucmVmZXJlbmNlcy5sZW5ndGggPiAwKSB7XG4gICAgICAgIGlmIChvcHRpb25zLnJlZmVyZW5jZXMubGVuZ3RoID4gMSkge1xuICAgICAgICAgIGlmIChfX0RFVl9fKSB7XG4gICAgICAgICAgICB0aGlzLmxvZ2dpbmdTZXJ2aWNlLmRlYnVnKCdFbGFzdGljIEFQTSBPcGVuVHJhY2luZzogVW5zdXBwb3J0ZWQgbnVtYmVyIG9mIHJlZmVyZW5jZXMsIG9ubHkgdGhlIGZpcnN0IGNoaWxkT2YgcmVmZXJlbmNlIHdpbGwgYmUgcmVjb3JkZWQuJyk7XG4gICAgICAgICAgfVxuICAgICAgICB9XG5cbiAgICAgICAgdmFyIGNoaWxkUmVmID0gZmluZChvcHRpb25zLnJlZmVyZW5jZXMsIGZ1bmN0aW9uIChyZWYpIHtcbiAgICAgICAgICByZXR1cm4gcmVmLnR5cGUoKSA9PT0gUkVGRVJFTkNFX0NISUxEX09GO1xuICAgICAgICB9KTtcblxuICAgICAgICBpZiAoY2hpbGRSZWYpIHtcbiAgICAgICAgICBzcGFuT3B0aW9ucy5wYXJlbnRJZCA9IGNoaWxkUmVmLnJlZmVyZW5jZWRDb250ZXh0KCkuaWQ7XG4gICAgICAgIH1cbiAgICAgIH1cbiAgICB9XG5cbiAgICB2YXIgc3BhbjtcbiAgICB2YXIgY3VycmVudFRyYW5zYWN0aW9uID0gdGhpcy50cmFuc2FjdGlvblNlcnZpY2UuZ2V0Q3VycmVudFRyYW5zYWN0aW9uKCk7XG5cbiAgICBpZiAoY3VycmVudFRyYW5zYWN0aW9uKSB7XG4gICAgICBzcGFuID0gdGhpcy50cmFuc2FjdGlvblNlcnZpY2Uuc3RhcnRTcGFuKG5hbWUsIHVuZGVmaW5lZCwgc3Bhbk9wdGlvbnMpO1xuICAgIH0gZWxzZSB7XG4gICAgICBzcGFuID0gdGhpcy50cmFuc2FjdGlvblNlcnZpY2Uuc3RhcnRUcmFuc2FjdGlvbihuYW1lLCB1bmRlZmluZWQsIHNwYW5PcHRpb25zKTtcbiAgICB9XG5cbiAgICBpZiAoIXNwYW4pIHtcbiAgICAgIHJldHVybiBuZXcgTm9vcFNwYW4oKTtcbiAgICB9XG5cbiAgICBpZiAoc3Bhbk9wdGlvbnMudGltZXN0YW1wKSB7XG4gICAgICBzcGFuLl9zdGFydCA9IHNwYW5PcHRpb25zLnRpbWVzdGFtcCAtIGdldFRpbWVPcmlnaW4oKTtcbiAgICB9XG5cbiAgICB2YXIgb3RTcGFuID0gbmV3IFNwYW4odGhpcywgc3Bhbik7XG5cbiAgICBpZiAob3B0aW9ucyAmJiBvcHRpb25zLnRhZ3MpIHtcbiAgICAgIG90U3Bhbi5hZGRUYWdzKG9wdGlvbnMudGFncyk7XG4gICAgfVxuXG4gICAgcmV0dXJuIG90U3BhbjtcbiAgfTtcblxuICBfcHJvdG8uX2luamVjdCA9IGZ1bmN0aW9uIF9pbmplY3Qoc3BhbkNvbnRleHQsIGZvcm1hdCwgY2Fycmllcikge1xuICAgIHN3aXRjaCAoZm9ybWF0KSB7XG4gICAgICBjYXNlIEZPUk1BVF9URVhUX01BUDpcbiAgICAgIGNhc2UgRk9STUFUX0hUVFBfSEVBREVSUzpcbiAgICAgICAgdGhpcy5wZXJmb3JtYW5jZU1vbml0b3JpbmcuaW5qZWN0RHRIZWFkZXIoc3BhbkNvbnRleHQsIGNhcnJpZXIpO1xuICAgICAgICBicmVhaztcblxuICAgICAgY2FzZSBGT1JNQVRfQklOQVJZOlxuICAgICAgICBpZiAoX19ERVZfXykge1xuICAgICAgICAgIHRoaXMubG9nZ2luZ1NlcnZpY2UuZGVidWcoJ0VsYXN0aWMgQVBNIE9wZW5UcmFjaW5nOiBiaW5hcnkgY2FycmllciBmb3JtYXQgaXMgbm90IHN1cHBvcnRlZC4nKTtcbiAgICAgICAgfVxuXG4gICAgICAgIGJyZWFrO1xuICAgIH1cbiAgfTtcblxuICBfcHJvdG8uX2V4dHJhY3QgPSBmdW5jdGlvbiBfZXh0cmFjdChmb3JtYXQsIGNhcnJpZXIpIHtcbiAgICB2YXIgY3R4O1xuXG4gICAgc3dpdGNoIChmb3JtYXQpIHtcbiAgICAgIGNhc2UgRk9STUFUX1RFWFRfTUFQOlxuICAgICAgY2FzZSBGT1JNQVRfSFRUUF9IRUFERVJTOlxuICAgICAgICBjdHggPSB0aGlzLnBlcmZvcm1hbmNlTW9uaXRvcmluZy5leHRyYWN0RHRIZWFkZXIoY2Fycmllcik7XG4gICAgICAgIGJyZWFrO1xuXG4gICAgICBjYXNlIEZPUk1BVF9CSU5BUlk6XG4gICAgICAgIGlmIChfX0RFVl9fKSB7XG4gICAgICAgICAgdGhpcy5sb2dnaW5nU2VydmljZS5kZWJ1ZygnRWxhc3RpYyBBUE0gT3BlblRyYWNpbmc6IGJpbmFyeSBjYXJyaWVyIGZvcm1hdCBpcyBub3Qgc3VwcG9ydGVkLicpO1xuICAgICAgICB9XG5cbiAgICAgICAgYnJlYWs7XG4gICAgfVxuXG4gICAgaWYgKCFjdHgpIHtcbiAgICAgIGN0eCA9IG51bGw7XG4gICAgfVxuXG4gICAgcmV0dXJuIGN0eDtcbiAgfTtcblxuICByZXR1cm4gVHJhY2VyO1xufShvdFRyYWNlcik7XG5cbmV4cG9ydCBkZWZhdWx0IFRyYWNlcjsiLCJpbXBvcnQgeyBnZXREdXJhdGlvbiwgUEVSRiB9IGZyb20gJy4uL2NvbW1vbi91dGlscyc7XG5pbXBvcnQgeyBQQUdFX0xPQUQsIFRSVU5DQVRFRF9UWVBFIH0gZnJvbSAnLi4vY29tbW9uL2NvbnN0YW50cyc7XG52YXIgcGFnZUxvYWRCcmVha2Rvd25zID0gW1snZG9tYWluTG9va3VwU3RhcnQnLCAnZG9tYWluTG9va3VwRW5kJywgJ0ROUyddLCBbJ2Nvbm5lY3RTdGFydCcsICdjb25uZWN0RW5kJywgJ1RDUCddLCBbJ3JlcXVlc3RTdGFydCcsICdyZXNwb25zZVN0YXJ0JywgJ1JlcXVlc3QnXSwgWydyZXNwb25zZVN0YXJ0JywgJ3Jlc3BvbnNlRW5kJywgJ1Jlc3BvbnNlJ10sIFsnZG9tTG9hZGluZycsICdkb21Db21wbGV0ZScsICdQcm9jZXNzaW5nJ10sIFsnbG9hZEV2ZW50U3RhcnQnLCAnbG9hZEV2ZW50RW5kJywgJ0xvYWQnXV07XG5cbmZ1bmN0aW9uIGdldFZhbHVlKHZhbHVlKSB7XG4gIHJldHVybiB7XG4gICAgdmFsdWU6IHZhbHVlXG4gIH07XG59XG5cbmZ1bmN0aW9uIGNhbGN1bGF0ZVNlbGZUaW1lKHRyYW5zYWN0aW9uKSB7XG4gIHZhciBzcGFucyA9IHRyYW5zYWN0aW9uLnNwYW5zLFxuICAgICAgX3N0YXJ0ID0gdHJhbnNhY3Rpb24uX3N0YXJ0LFxuICAgICAgX2VuZCA9IHRyYW5zYWN0aW9uLl9lbmQ7XG5cbiAgaWYgKHNwYW5zLmxlbmd0aCA9PT0gMCkge1xuICAgIHJldHVybiB0cmFuc2FjdGlvbi5kdXJhdGlvbigpO1xuICB9XG5cbiAgc3BhbnMuc29ydChmdW5jdGlvbiAoc3BhbjEsIHNwYW4yKSB7XG4gICAgcmV0dXJuIHNwYW4xLl9zdGFydCAtIHNwYW4yLl9zdGFydDtcbiAgfSk7XG4gIHZhciBzcGFuID0gc3BhbnNbMF07XG4gIHZhciBzcGFuRW5kID0gc3Bhbi5fZW5kO1xuICB2YXIgc3BhblN0YXJ0ID0gc3Bhbi5fc3RhcnQ7XG4gIHZhciBsYXN0Q29udGludW91c0VuZCA9IHNwYW5FbmQ7XG4gIHZhciBzZWxmVGltZSA9IHNwYW5TdGFydCAtIF9zdGFydDtcblxuICBmb3IgKHZhciBpID0gMTsgaSA8IHNwYW5zLmxlbmd0aDsgaSsrKSB7XG4gICAgc3BhbiA9IHNwYW5zW2ldO1xuICAgIHNwYW5TdGFydCA9IHNwYW4uX3N0YXJ0O1xuICAgIHNwYW5FbmQgPSBzcGFuLl9lbmQ7XG5cbiAgICBpZiAoc3BhblN0YXJ0ID4gbGFzdENvbnRpbnVvdXNFbmQpIHtcbiAgICAgIHNlbGZUaW1lICs9IHNwYW5TdGFydCAtIGxhc3RDb250aW51b3VzRW5kO1xuICAgICAgbGFzdENvbnRpbnVvdXNFbmQgPSBzcGFuRW5kO1xuICAgIH0gZWxzZSBpZiAoc3BhbkVuZCA+IGxhc3RDb250aW51b3VzRW5kKSB7XG4gICAgICBsYXN0Q29udGludW91c0VuZCA9IHNwYW5FbmQ7XG4gICAgfVxuICB9XG5cbiAgaWYgKGxhc3RDb250aW51b3VzRW5kIDwgX2VuZCkge1xuICAgIHNlbGZUaW1lICs9IF9lbmQgLSBsYXN0Q29udGludW91c0VuZDtcbiAgfVxuXG4gIHJldHVybiBzZWxmVGltZTtcbn1cblxuZnVuY3Rpb24gZ3JvdXBTcGFucyh0cmFuc2FjdGlvbikge1xuICB2YXIgc3Bhbk1hcCA9IHt9O1xuICB2YXIgdHJhbnNhY3Rpb25TZWxmVGltZSA9IGNhbGN1bGF0ZVNlbGZUaW1lKHRyYW5zYWN0aW9uKTtcbiAgc3Bhbk1hcFsnYXBwJ10gPSB7XG4gICAgY291bnQ6IDEsXG4gICAgZHVyYXRpb246IHRyYW5zYWN0aW9uU2VsZlRpbWVcbiAgfTtcbiAgdmFyIHNwYW5zID0gdHJhbnNhY3Rpb24uc3BhbnM7XG5cbiAgZm9yICh2YXIgaSA9IDA7IGkgPCBzcGFucy5sZW5ndGg7IGkrKykge1xuICAgIHZhciBzcGFuID0gc3BhbnNbaV07XG4gICAgdmFyIGR1cmF0aW9uID0gc3Bhbi5kdXJhdGlvbigpO1xuXG4gICAgaWYgKGR1cmF0aW9uID09PSAwIHx8IGR1cmF0aW9uID09IG51bGwpIHtcbiAgICAgIGNvbnRpbnVlO1xuICAgIH1cblxuICAgIHZhciB0eXBlID0gc3Bhbi50eXBlLFxuICAgICAgICBzdWJ0eXBlID0gc3Bhbi5zdWJ0eXBlO1xuICAgIHZhciBrZXkgPSB0eXBlLnJlcGxhY2UoVFJVTkNBVEVEX1RZUEUsICcnKTtcblxuICAgIGlmIChzdWJ0eXBlKSB7XG4gICAgICBrZXkgKz0gJy4nICsgc3VidHlwZTtcbiAgICB9XG5cbiAgICBpZiAoIXNwYW5NYXBba2V5XSkge1xuICAgICAgc3Bhbk1hcFtrZXldID0ge1xuICAgICAgICBkdXJhdGlvbjogMCxcbiAgICAgICAgY291bnQ6IDBcbiAgICAgIH07XG4gICAgfVxuXG4gICAgc3Bhbk1hcFtrZXldLmNvdW50Kys7XG4gICAgc3Bhbk1hcFtrZXldLmR1cmF0aW9uICs9IGR1cmF0aW9uO1xuICB9XG5cbiAgcmV0dXJuIHNwYW5NYXA7XG59XG5cbmZ1bmN0aW9uIGdldFNwYW5CcmVha2Rvd24odHJhbnNhY3Rpb25EZXRhaWxzLCBfcmVmKSB7XG4gIHZhciBkZXRhaWxzID0gX3JlZi5kZXRhaWxzLFxuICAgICAgX3JlZiRjb3VudCA9IF9yZWYuY291bnQsXG4gICAgICBjb3VudCA9IF9yZWYkY291bnQgPT09IHZvaWQgMCA/IDEgOiBfcmVmJGNvdW50LFxuICAgICAgZHVyYXRpb24gPSBfcmVmLmR1cmF0aW9uO1xuICByZXR1cm4ge1xuICAgIHRyYW5zYWN0aW9uOiB0cmFuc2FjdGlvbkRldGFpbHMsXG4gICAgc3BhbjogZGV0YWlscyxcbiAgICBzYW1wbGVzOiB7XG4gICAgICAnc3Bhbi5zZWxmX3RpbWUuY291bnQnOiBnZXRWYWx1ZShjb3VudCksXG4gICAgICAnc3Bhbi5zZWxmX3RpbWUuc3VtLnVzJzogZ2V0VmFsdWUoZHVyYXRpb24pXG4gICAgfVxuICB9O1xufVxuXG5leHBvcnQgZnVuY3Rpb24gY2FwdHVyZUJyZWFrZG93bih0cmFuc2FjdGlvbiwgdGltaW5ncykge1xuICBpZiAodGltaW5ncyA9PT0gdm9pZCAwKSB7XG4gICAgdGltaW5ncyA9IFBFUkYudGltaW5nO1xuICB9XG5cbiAgdmFyIGJyZWFrZG93bnMgPSBbXTtcbiAgdmFyIHRyRHVyYXRpb24gPSB0cmFuc2FjdGlvbi5kdXJhdGlvbigpO1xuICB2YXIgbmFtZSA9IHRyYW5zYWN0aW9uLm5hbWUsXG4gICAgICB0eXBlID0gdHJhbnNhY3Rpb24udHlwZSxcbiAgICAgIHNhbXBsZWQgPSB0cmFuc2FjdGlvbi5zYW1wbGVkO1xuICB2YXIgdHJhbnNhY3Rpb25EZXRhaWxzID0ge1xuICAgIG5hbWU6IG5hbWUsXG4gICAgdHlwZTogdHlwZVxuICB9O1xuICBicmVha2Rvd25zLnB1c2goe1xuICAgIHRyYW5zYWN0aW9uOiB0cmFuc2FjdGlvbkRldGFpbHMsXG4gICAgc2FtcGxlczoge1xuICAgICAgJ3RyYW5zYWN0aW9uLmR1cmF0aW9uLmNvdW50JzogZ2V0VmFsdWUoMSksXG4gICAgICAndHJhbnNhY3Rpb24uZHVyYXRpb24uc3VtLnVzJzogZ2V0VmFsdWUodHJEdXJhdGlvbiksXG4gICAgICAndHJhbnNhY3Rpb24uYnJlYWtkb3duLmNvdW50JzogZ2V0VmFsdWUoc2FtcGxlZCA/IDEgOiAwKVxuICAgIH1cbiAgfSk7XG5cbiAgaWYgKCFzYW1wbGVkKSB7XG4gICAgcmV0dXJuIGJyZWFrZG93bnM7XG4gIH1cblxuICBpZiAodHlwZSA9PT0gUEFHRV9MT0FEICYmIHRpbWluZ3MpIHtcbiAgICBmb3IgKHZhciBpID0gMDsgaSA8IHBhZ2VMb2FkQnJlYWtkb3ducy5sZW5ndGg7IGkrKykge1xuICAgICAgdmFyIGN1cnJlbnQgPSBwYWdlTG9hZEJyZWFrZG93bnNbaV07XG4gICAgICB2YXIgc3RhcnQgPSB0aW1pbmdzW2N1cnJlbnRbMF1dO1xuICAgICAgdmFyIGVuZCA9IHRpbWluZ3NbY3VycmVudFsxXV07XG4gICAgICB2YXIgZHVyYXRpb24gPSBnZXREdXJhdGlvbihzdGFydCwgZW5kKTtcblxuICAgICAgaWYgKGR1cmF0aW9uID09PSAwIHx8IGR1cmF0aW9uID09IG51bGwpIHtcbiAgICAgICAgY29udGludWU7XG4gICAgICB9XG5cbiAgICAgIGJyZWFrZG93bnMucHVzaChnZXRTcGFuQnJlYWtkb3duKHRyYW5zYWN0aW9uRGV0YWlscywge1xuICAgICAgICBkZXRhaWxzOiB7XG4gICAgICAgICAgdHlwZTogY3VycmVudFsyXVxuICAgICAgICB9LFxuICAgICAgICBkdXJhdGlvbjogZHVyYXRpb25cbiAgICAgIH0pKTtcbiAgICB9XG4gIH0gZWxzZSB7XG4gICAgdmFyIHNwYW5NYXAgPSBncm91cFNwYW5zKHRyYW5zYWN0aW9uKTtcbiAgICBPYmplY3Qua2V5cyhzcGFuTWFwKS5mb3JFYWNoKGZ1bmN0aW9uIChrZXkpIHtcbiAgICAgIHZhciBfa2V5JHNwbGl0ID0ga2V5LnNwbGl0KCcuJyksXG4gICAgICAgICAgdHlwZSA9IF9rZXkkc3BsaXRbMF0sXG4gICAgICAgICAgc3VidHlwZSA9IF9rZXkkc3BsaXRbMV07XG5cbiAgICAgIHZhciBfc3Bhbk1hcCRrZXkgPSBzcGFuTWFwW2tleV0sXG4gICAgICAgICAgZHVyYXRpb24gPSBfc3Bhbk1hcCRrZXkuZHVyYXRpb24sXG4gICAgICAgICAgY291bnQgPSBfc3Bhbk1hcCRrZXkuY291bnQ7XG4gICAgICBicmVha2Rvd25zLnB1c2goZ2V0U3BhbkJyZWFrZG93bih0cmFuc2FjdGlvbkRldGFpbHMsIHtcbiAgICAgICAgZGV0YWlsczoge1xuICAgICAgICAgIHR5cGU6IHR5cGUsXG4gICAgICAgICAgc3VidHlwZTogc3VidHlwZVxuICAgICAgICB9LFxuICAgICAgICBkdXJhdGlvbjogZHVyYXRpb24sXG4gICAgICAgIGNvdW50OiBjb3VudFxuICAgICAgfSkpO1xuICAgIH0pO1xuICB9XG5cbiAgcmV0dXJuIGJyZWFrZG93bnM7XG59IiwiaW1wb3J0IFNwYW4gZnJvbSAnLi9zcGFuJztcbmltcG9ydCB7IFJFU09VUkNFX0lOSVRJQVRPUl9UWVBFUywgTUFYX1NQQU5fRFVSQVRJT04sIFVTRVJfVElNSU5HX1RIUkVTSE9MRCwgUEFHRV9MT0FELCBSRVNPVVJDRSwgTUVBU1VSRSB9IGZyb20gJy4uL2NvbW1vbi9jb25zdGFudHMnO1xuaW1wb3J0IHsgc3RyaXBRdWVyeVN0cmluZ0Zyb21VcmwsIFBFUkYsIGlzUGVyZlRpbWVsaW5lU3VwcG9ydGVkIH0gZnJvbSAnLi4vY29tbW9uL3V0aWxzJztcbmltcG9ydCB7IHN0YXRlIH0gZnJvbSAnLi4vc3RhdGUnO1xudmFyIGV2ZW50UGFpcnMgPSBbWydkb21haW5Mb29rdXBTdGFydCcsICdkb21haW5Mb29rdXBFbmQnLCAnRG9tYWluIGxvb2t1cCddLCBbJ2Nvbm5lY3RTdGFydCcsICdjb25uZWN0RW5kJywgJ01ha2luZyBhIGNvbm5lY3Rpb24gdG8gdGhlIHNlcnZlciddLCBbJ3JlcXVlc3RTdGFydCcsICdyZXNwb25zZUVuZCcsICdSZXF1ZXN0aW5nIGFuZCByZWNlaXZpbmcgdGhlIGRvY3VtZW50J10sIFsnZG9tTG9hZGluZycsICdkb21JbnRlcmFjdGl2ZScsICdQYXJzaW5nIHRoZSBkb2N1bWVudCwgZXhlY3V0aW5nIHN5bmMuIHNjcmlwdHMnXSwgWydkb21Db250ZW50TG9hZGVkRXZlbnRTdGFydCcsICdkb21Db250ZW50TG9hZGVkRXZlbnRFbmQnLCAnRmlyZSBcIkRPTUNvbnRlbnRMb2FkZWRcIiBldmVudCddLCBbJ2xvYWRFdmVudFN0YXJ0JywgJ2xvYWRFdmVudEVuZCcsICdGaXJlIFwibG9hZFwiIGV2ZW50J11dO1xuXG5mdW5jdGlvbiBzaG91bGRDcmVhdGVTcGFuKHN0YXJ0LCBlbmQsIHRyU3RhcnQsIHRyRW5kLCBiYXNlVGltZSkge1xuICBpZiAoYmFzZVRpbWUgPT09IHZvaWQgMCkge1xuICAgIGJhc2VUaW1lID0gMDtcbiAgfVxuXG4gIHJldHVybiB0eXBlb2Ygc3RhcnQgPT09ICdudW1iZXInICYmIHR5cGVvZiBlbmQgPT09ICdudW1iZXInICYmIHN0YXJ0ID49IGJhc2VUaW1lICYmIGVuZCA+IHN0YXJ0ICYmIHN0YXJ0IC0gYmFzZVRpbWUgPj0gdHJTdGFydCAmJiBlbmQgLSBiYXNlVGltZSA8PSB0ckVuZCAmJiBlbmQgLSBzdGFydCA8IE1BWF9TUEFOX0RVUkFUSU9OICYmIHN0YXJ0IC0gYmFzZVRpbWUgPCBNQVhfU1BBTl9EVVJBVElPTiAmJiBlbmQgLSBiYXNlVGltZSA8IE1BWF9TUEFOX0RVUkFUSU9OO1xufVxuXG5mdW5jdGlvbiBjcmVhdGVOYXZpZ2F0aW9uVGltaW5nU3BhbnModGltaW5ncywgYmFzZVRpbWUsIHRyU3RhcnQsIHRyRW5kKSB7XG4gIHZhciBzcGFucyA9IFtdO1xuXG4gIGZvciAodmFyIGkgPSAwOyBpIDwgZXZlbnRQYWlycy5sZW5ndGg7IGkrKykge1xuICAgIHZhciBzdGFydCA9IHRpbWluZ3NbZXZlbnRQYWlyc1tpXVswXV07XG4gICAgdmFyIGVuZCA9IHRpbWluZ3NbZXZlbnRQYWlyc1tpXVsxXV07XG5cbiAgICBpZiAoIXNob3VsZENyZWF0ZVNwYW4oc3RhcnQsIGVuZCwgdHJTdGFydCwgdHJFbmQsIGJhc2VUaW1lKSkge1xuICAgICAgY29udGludWU7XG4gICAgfVxuXG4gICAgdmFyIHNwYW4gPSBuZXcgU3BhbihldmVudFBhaXJzW2ldWzJdLCAnaGFyZC1uYXZpZ2F0aW9uLmJyb3dzZXItdGltaW5nJyk7XG4gICAgdmFyIGRhdGEgPSBudWxsO1xuXG4gICAgaWYgKGV2ZW50UGFpcnNbaV1bMF0gPT09ICdyZXF1ZXN0U3RhcnQnKSB7XG4gICAgICBzcGFuLnBhZ2VSZXNwb25zZSA9IHRydWU7XG4gICAgICBkYXRhID0ge1xuICAgICAgICB1cmw6IGxvY2F0aW9uLm9yaWdpblxuICAgICAgfTtcbiAgICB9XG5cbiAgICBzcGFuLl9zdGFydCA9IHN0YXJ0IC0gYmFzZVRpbWU7XG4gICAgc3Bhbi5lbmQoZW5kIC0gYmFzZVRpbWUsIGRhdGEpO1xuICAgIHNwYW5zLnB1c2goc3Bhbik7XG4gIH1cblxuICByZXR1cm4gc3BhbnM7XG59XG5cbmZ1bmN0aW9uIGNyZWF0ZVJlc291cmNlVGltaW5nU3BhbihyZXNvdXJjZVRpbWluZ0VudHJ5KSB7XG4gIHZhciBuYW1lID0gcmVzb3VyY2VUaW1pbmdFbnRyeS5uYW1lLFxuICAgICAgaW5pdGlhdG9yVHlwZSA9IHJlc291cmNlVGltaW5nRW50cnkuaW5pdGlhdG9yVHlwZSxcbiAgICAgIHN0YXJ0VGltZSA9IHJlc291cmNlVGltaW5nRW50cnkuc3RhcnRUaW1lLFxuICAgICAgcmVzcG9uc2VFbmQgPSByZXNvdXJjZVRpbWluZ0VudHJ5LnJlc3BvbnNlRW5kO1xuICB2YXIga2luZCA9ICdyZXNvdXJjZSc7XG5cbiAgaWYgKGluaXRpYXRvclR5cGUpIHtcbiAgICBraW5kICs9ICcuJyArIGluaXRpYXRvclR5cGU7XG4gIH1cblxuICB2YXIgc3Bhbk5hbWUgPSBzdHJpcFF1ZXJ5U3RyaW5nRnJvbVVybChuYW1lKTtcbiAgdmFyIHNwYW4gPSBuZXcgU3BhbihzcGFuTmFtZSwga2luZCk7XG4gIHNwYW4uX3N0YXJ0ID0gc3RhcnRUaW1lO1xuICBzcGFuLmVuZChyZXNwb25zZUVuZCwge1xuICAgIHVybDogbmFtZSxcbiAgICBlbnRyeTogcmVzb3VyY2VUaW1pbmdFbnRyeVxuICB9KTtcbiAgcmV0dXJuIHNwYW47XG59XG5cbmZ1bmN0aW9uIGlzQ2FwdHVyZWRCeVBhdGNoaW5nKHJlc291cmNlU3RhcnRUaW1lLCByZXF1ZXN0UGF0Y2hUaW1lKSB7XG4gIHJldHVybiByZXF1ZXN0UGF0Y2hUaW1lICE9IG51bGwgJiYgcmVzb3VyY2VTdGFydFRpbWUgPiByZXF1ZXN0UGF0Y2hUaW1lO1xufVxuXG5mdW5jdGlvbiBpc0ludGFrZUFQSUVuZHBvaW50KHVybCkge1xuICByZXR1cm4gL2ludGFrZVxcL3ZcXGQrXFwvcnVtXFwvZXZlbnRzLy50ZXN0KHVybCk7XG59XG5cbmZ1bmN0aW9uIGNyZWF0ZVJlc291cmNlVGltaW5nU3BhbnMoZW50cmllcywgcmVxdWVzdFBhdGNoVGltZSwgdHJTdGFydCwgdHJFbmQpIHtcbiAgdmFyIHNwYW5zID0gW107XG5cbiAgZm9yICh2YXIgaSA9IDA7IGkgPCBlbnRyaWVzLmxlbmd0aDsgaSsrKSB7XG4gICAgdmFyIF9lbnRyaWVzJGkgPSBlbnRyaWVzW2ldLFxuICAgICAgICBpbml0aWF0b3JUeXBlID0gX2VudHJpZXMkaS5pbml0aWF0b3JUeXBlLFxuICAgICAgICBuYW1lID0gX2VudHJpZXMkaS5uYW1lLFxuICAgICAgICBzdGFydFRpbWUgPSBfZW50cmllcyRpLnN0YXJ0VGltZSxcbiAgICAgICAgcmVzcG9uc2VFbmQgPSBfZW50cmllcyRpLnJlc3BvbnNlRW5kO1xuXG4gICAgaWYgKFJFU09VUkNFX0lOSVRJQVRPUl9UWVBFUy5pbmRleE9mKGluaXRpYXRvclR5cGUpID09PSAtMSB8fCBuYW1lID09IG51bGwpIHtcbiAgICAgIGNvbnRpbnVlO1xuICAgIH1cblxuICAgIGlmICgoaW5pdGlhdG9yVHlwZSA9PT0gJ3htbGh0dHByZXF1ZXN0JyB8fCBpbml0aWF0b3JUeXBlID09PSAnZmV0Y2gnKSAmJiAoaXNJbnRha2VBUElFbmRwb2ludChuYW1lKSB8fCBpc0NhcHR1cmVkQnlQYXRjaGluZyhzdGFydFRpbWUsIHJlcXVlc3RQYXRjaFRpbWUpKSkge1xuICAgICAgY29udGludWU7XG4gICAgfVxuXG4gICAgaWYgKHNob3VsZENyZWF0ZVNwYW4oc3RhcnRUaW1lLCByZXNwb25zZUVuZCwgdHJTdGFydCwgdHJFbmQpKSB7XG4gICAgICBzcGFucy5wdXNoKGNyZWF0ZVJlc291cmNlVGltaW5nU3BhbihlbnRyaWVzW2ldKSk7XG4gICAgfVxuICB9XG5cbiAgcmV0dXJuIHNwYW5zO1xufVxuXG5mdW5jdGlvbiBjcmVhdGVVc2VyVGltaW5nU3BhbnMoZW50cmllcywgdHJTdGFydCwgdHJFbmQpIHtcbiAgdmFyIHVzZXJUaW1pbmdTcGFucyA9IFtdO1xuXG4gIGZvciAodmFyIGkgPSAwOyBpIDwgZW50cmllcy5sZW5ndGg7IGkrKykge1xuICAgIHZhciBfZW50cmllcyRpMiA9IGVudHJpZXNbaV0sXG4gICAgICAgIG5hbWUgPSBfZW50cmllcyRpMi5uYW1lLFxuICAgICAgICBzdGFydFRpbWUgPSBfZW50cmllcyRpMi5zdGFydFRpbWUsXG4gICAgICAgIGR1cmF0aW9uID0gX2VudHJpZXMkaTIuZHVyYXRpb247XG4gICAgdmFyIGVuZCA9IHN0YXJ0VGltZSArIGR1cmF0aW9uO1xuXG4gICAgaWYgKGR1cmF0aW9uIDw9IFVTRVJfVElNSU5HX1RIUkVTSE9MRCB8fCAhc2hvdWxkQ3JlYXRlU3BhbihzdGFydFRpbWUsIGVuZCwgdHJTdGFydCwgdHJFbmQpKSB7XG4gICAgICBjb250aW51ZTtcbiAgICB9XG5cbiAgICB2YXIga2luZCA9ICdhcHAnO1xuICAgIHZhciBzcGFuID0gbmV3IFNwYW4obmFtZSwga2luZCk7XG4gICAgc3Bhbi5fc3RhcnQgPSBzdGFydFRpbWU7XG4gICAgc3Bhbi5lbmQoZW5kKTtcbiAgICB1c2VyVGltaW5nU3BhbnMucHVzaChzcGFuKTtcbiAgfVxuXG4gIHJldHVybiB1c2VyVGltaW5nU3BhbnM7XG59XG5cbnZhciBOQVZJR0FUSU9OX1RJTUlOR19NQVJLUyA9IFsnZmV0Y2hTdGFydCcsICdkb21haW5Mb29rdXBTdGFydCcsICdkb21haW5Mb29rdXBFbmQnLCAnY29ubmVjdFN0YXJ0JywgJ2Nvbm5lY3RFbmQnLCAncmVxdWVzdFN0YXJ0JywgJ3Jlc3BvbnNlU3RhcnQnLCAncmVzcG9uc2VFbmQnLCAnZG9tTG9hZGluZycsICdkb21JbnRlcmFjdGl2ZScsICdkb21Db250ZW50TG9hZGVkRXZlbnRTdGFydCcsICdkb21Db250ZW50TG9hZGVkRXZlbnRFbmQnLCAnZG9tQ29tcGxldGUnLCAnbG9hZEV2ZW50U3RhcnQnLCAnbG9hZEV2ZW50RW5kJ107XG52YXIgQ09NUFJFU1NFRF9OQVZfVElNSU5HX01BUktTID0gWydmcycsICdscycsICdsZScsICdjcycsICdjZScsICdxcycsICdycycsICdyZScsICdkbCcsICdkaScsICdkcycsICdkZScsICdkYycsICdlcycsICdlZSddO1xuXG5mdW5jdGlvbiBnZXROYXZpZ2F0aW9uVGltaW5nTWFya3ModGltaW5nKSB7XG4gIHZhciBmZXRjaFN0YXJ0ID0gdGltaW5nLmZldGNoU3RhcnQsXG4gICAgICBuYXZpZ2F0aW9uU3RhcnQgPSB0aW1pbmcubmF2aWdhdGlvblN0YXJ0LFxuICAgICAgcmVzcG9uc2VTdGFydCA9IHRpbWluZy5yZXNwb25zZVN0YXJ0LFxuICAgICAgcmVzcG9uc2VFbmQgPSB0aW1pbmcucmVzcG9uc2VFbmQ7XG5cbiAgaWYgKGZldGNoU3RhcnQgPj0gbmF2aWdhdGlvblN0YXJ0ICYmIHJlc3BvbnNlU3RhcnQgPj0gZmV0Y2hTdGFydCAmJiByZXNwb25zZUVuZCA+PSByZXNwb25zZVN0YXJ0KSB7XG4gICAgdmFyIG1hcmtzID0ge307XG4gICAgTkFWSUdBVElPTl9USU1JTkdfTUFSS1MuZm9yRWFjaChmdW5jdGlvbiAodGltaW5nS2V5KSB7XG4gICAgICB2YXIgbSA9IHRpbWluZ1t0aW1pbmdLZXldO1xuXG4gICAgICBpZiAobSAmJiBtID49IGZldGNoU3RhcnQpIHtcbiAgICAgICAgbWFya3NbdGltaW5nS2V5XSA9IHBhcnNlSW50KG0gLSBmZXRjaFN0YXJ0KTtcbiAgICAgIH1cbiAgICB9KTtcbiAgICByZXR1cm4gbWFya3M7XG4gIH1cblxuICByZXR1cm4gbnVsbDtcbn1cblxuZnVuY3Rpb24gZ2V0UGFnZUxvYWRNYXJrcyh0aW1pbmcpIHtcbiAgdmFyIG1hcmtzID0gZ2V0TmF2aWdhdGlvblRpbWluZ01hcmtzKHRpbWluZyk7XG5cbiAgaWYgKG1hcmtzID09IG51bGwpIHtcbiAgICByZXR1cm4gbnVsbDtcbiAgfVxuXG4gIHJldHVybiB7XG4gICAgbmF2aWdhdGlvblRpbWluZzogbWFya3MsXG4gICAgYWdlbnQ6IHtcbiAgICAgIHRpbWVUb0ZpcnN0Qnl0ZTogbWFya3MucmVzcG9uc2VTdGFydCxcbiAgICAgIGRvbUludGVyYWN0aXZlOiBtYXJrcy5kb21JbnRlcmFjdGl2ZSxcbiAgICAgIGRvbUNvbXBsZXRlOiBtYXJrcy5kb21Db21wbGV0ZVxuICAgIH1cbiAgfTtcbn1cblxuZnVuY3Rpb24gY2FwdHVyZU5hdmlnYXRpb24odHJhbnNhY3Rpb24pIHtcbiAgaWYgKCF0cmFuc2FjdGlvbi5jYXB0dXJlVGltaW5ncykge1xuICAgIHJldHVybjtcbiAgfVxuXG4gIHZhciB0ckVuZCA9IHRyYW5zYWN0aW9uLl9lbmQ7XG5cbiAgaWYgKHRyYW5zYWN0aW9uLnR5cGUgPT09IFBBR0VfTE9BRCkge1xuICAgIGlmICh0cmFuc2FjdGlvbi5tYXJrcyAmJiB0cmFuc2FjdGlvbi5tYXJrcy5jdXN0b20pIHtcbiAgICAgIHZhciBjdXN0b21NYXJrcyA9IHRyYW5zYWN0aW9uLm1hcmtzLmN1c3RvbTtcbiAgICAgIE9iamVjdC5rZXlzKGN1c3RvbU1hcmtzKS5mb3JFYWNoKGZ1bmN0aW9uIChrZXkpIHtcbiAgICAgICAgY3VzdG9tTWFya3Nba2V5XSArPSB0cmFuc2FjdGlvbi5fc3RhcnQ7XG4gICAgICB9KTtcbiAgICB9XG5cbiAgICB2YXIgdHJTdGFydCA9IDA7XG4gICAgdHJhbnNhY3Rpb24uX3N0YXJ0ID0gdHJTdGFydDtcbiAgICB2YXIgdGltaW5ncyA9IFBFUkYudGltaW5nO1xuICAgIGNyZWF0ZU5hdmlnYXRpb25UaW1pbmdTcGFucyh0aW1pbmdzLCB0aW1pbmdzLmZldGNoU3RhcnQsIHRyU3RhcnQsIHRyRW5kKS5mb3JFYWNoKGZ1bmN0aW9uIChzcGFuKSB7XG4gICAgICBzcGFuLnRyYWNlSWQgPSB0cmFuc2FjdGlvbi50cmFjZUlkO1xuICAgICAgc3Bhbi5zYW1wbGVkID0gdHJhbnNhY3Rpb24uc2FtcGxlZDtcblxuICAgICAgaWYgKHNwYW4ucGFnZVJlc3BvbnNlICYmIHRyYW5zYWN0aW9uLm9wdGlvbnMucGFnZUxvYWRTcGFuSWQpIHtcbiAgICAgICAgc3Bhbi5pZCA9IHRyYW5zYWN0aW9uLm9wdGlvbnMucGFnZUxvYWRTcGFuSWQ7XG4gICAgICB9XG5cbiAgICAgIHRyYW5zYWN0aW9uLnNwYW5zLnB1c2goc3Bhbik7XG4gICAgfSk7XG4gICAgdHJhbnNhY3Rpb24uYWRkTWFya3MoZ2V0UGFnZUxvYWRNYXJrcyh0aW1pbmdzKSk7XG4gIH1cblxuICBpZiAoaXNQZXJmVGltZWxpbmVTdXBwb3J0ZWQoKSkge1xuICAgIHZhciBfdHJTdGFydCA9IHRyYW5zYWN0aW9uLl9zdGFydDtcbiAgICB2YXIgcmVzb3VyY2VFbnRyaWVzID0gUEVSRi5nZXRFbnRyaWVzQnlUeXBlKFJFU09VUkNFKTtcbiAgICBjcmVhdGVSZXNvdXJjZVRpbWluZ1NwYW5zKHJlc291cmNlRW50cmllcywgc3RhdGUuYm9vdHN0cmFwVGltZSwgX3RyU3RhcnQsIHRyRW5kKS5mb3JFYWNoKGZ1bmN0aW9uIChzcGFuKSB7XG4gICAgICByZXR1cm4gdHJhbnNhY3Rpb24uc3BhbnMucHVzaChzcGFuKTtcbiAgICB9KTtcbiAgICB2YXIgdXNlckVudHJpZXMgPSBQRVJGLmdldEVudHJpZXNCeVR5cGUoTUVBU1VSRSk7XG4gICAgY3JlYXRlVXNlclRpbWluZ1NwYW5zKHVzZXJFbnRyaWVzLCBfdHJTdGFydCwgdHJFbmQpLmZvckVhY2goZnVuY3Rpb24gKHNwYW4pIHtcbiAgICAgIHJldHVybiB0cmFuc2FjdGlvbi5zcGFucy5wdXNoKHNwYW4pO1xuICAgIH0pO1xuICB9XG59XG5cbmV4cG9ydCB7IGdldFBhZ2VMb2FkTWFya3MsIGNhcHR1cmVOYXZpZ2F0aW9uLCBjcmVhdGVOYXZpZ2F0aW9uVGltaW5nU3BhbnMsIGNyZWF0ZVJlc291cmNlVGltaW5nU3BhbnMsIGNyZWF0ZVVzZXJUaW1pbmdTcGFucywgTkFWSUdBVElPTl9USU1JTkdfTUFSS1MsIENPTVBSRVNTRURfTkFWX1RJTUlOR19NQVJLUyB9OyIsImltcG9ydCBQZXJmb3JtYW5jZU1vbml0b3JpbmcgZnJvbSAnLi9wZXJmb3JtYW5jZS1tb25pdG9yaW5nJztcbmltcG9ydCBUcmFuc2FjdGlvblNlcnZpY2UgZnJvbSAnLi90cmFuc2FjdGlvbi1zZXJ2aWNlJztcbmltcG9ydCB7IEFQTV9TRVJWRVIsIENPTkZJR19TRVJWSUNFLCBMT0dHSU5HX1NFUlZJQ0UsIFRSQU5TQUNUSU9OX1NFUlZJQ0UsIFBFUkZPUk1BTkNFX01PTklUT1JJTkcgfSBmcm9tICcuLi9jb21tb24vY29uc3RhbnRzJztcbmltcG9ydCB7IHNlcnZpY2VDcmVhdG9ycyB9IGZyb20gJy4uL2NvbW1vbi9zZXJ2aWNlLWZhY3RvcnknO1xuXG5mdW5jdGlvbiByZWdpc3RlclNlcnZpY2VzKCkge1xuICBzZXJ2aWNlQ3JlYXRvcnNbVFJBTlNBQ1RJT05fU0VSVklDRV0gPSBmdW5jdGlvbiAoc2VydmljZUZhY3RvcnkpIHtcbiAgICB2YXIgX3NlcnZpY2VGYWN0b3J5JGdldFNlID0gc2VydmljZUZhY3RvcnkuZ2V0U2VydmljZShbTE9HR0lOR19TRVJWSUNFLCBDT05GSUdfU0VSVklDRV0pLFxuICAgICAgICBsb2dnaW5nU2VydmljZSA9IF9zZXJ2aWNlRmFjdG9yeSRnZXRTZVswXSxcbiAgICAgICAgY29uZmlnU2VydmljZSA9IF9zZXJ2aWNlRmFjdG9yeSRnZXRTZVsxXTtcblxuICAgIHJldHVybiBuZXcgVHJhbnNhY3Rpb25TZXJ2aWNlKGxvZ2dpbmdTZXJ2aWNlLCBjb25maWdTZXJ2aWNlKTtcbiAgfTtcblxuICBzZXJ2aWNlQ3JlYXRvcnNbUEVSRk9STUFOQ0VfTU9OSVRPUklOR10gPSBmdW5jdGlvbiAoc2VydmljZUZhY3RvcnkpIHtcbiAgICB2YXIgX3NlcnZpY2VGYWN0b3J5JGdldFNlMiA9IHNlcnZpY2VGYWN0b3J5LmdldFNlcnZpY2UoW0FQTV9TRVJWRVIsIENPTkZJR19TRVJWSUNFLCBMT0dHSU5HX1NFUlZJQ0UsIFRSQU5TQUNUSU9OX1NFUlZJQ0VdKSxcbiAgICAgICAgYXBtU2VydmVyID0gX3NlcnZpY2VGYWN0b3J5JGdldFNlMlswXSxcbiAgICAgICAgY29uZmlnU2VydmljZSA9IF9zZXJ2aWNlRmFjdG9yeSRnZXRTZTJbMV0sXG4gICAgICAgIGxvZ2dpbmdTZXJ2aWNlID0gX3NlcnZpY2VGYWN0b3J5JGdldFNlMlsyXSxcbiAgICAgICAgdHJhbnNhY3Rpb25TZXJ2aWNlID0gX3NlcnZpY2VGYWN0b3J5JGdldFNlMlszXTtcblxuICAgIHJldHVybiBuZXcgUGVyZm9ybWFuY2VNb25pdG9yaW5nKGFwbVNlcnZlciwgY29uZmlnU2VydmljZSwgbG9nZ2luZ1NlcnZpY2UsIHRyYW5zYWN0aW9uU2VydmljZSk7XG4gIH07XG59XG5cbmV4cG9ydCB7IHJlZ2lzdGVyU2VydmljZXMgfTsiLCJpbXBvcnQgeyBMT05HX1RBU0ssIExBUkdFU1RfQ09OVEVOVEZVTF9QQUlOVCwgRklSU1RfQ09OVEVOVEZVTF9QQUlOVCwgRklSU1RfSU5QVVQsIExBWU9VVF9TSElGVCB9IGZyb20gJy4uL2NvbW1vbi9jb25zdGFudHMnO1xuaW1wb3J0IHsgbm9vcCwgUEVSRiB9IGZyb20gJy4uL2NvbW1vbi91dGlscyc7XG5pbXBvcnQgU3BhbiBmcm9tICcuL3NwYW4nO1xuZXhwb3J0IHZhciBtZXRyaWNzID0ge1xuICBmaWQ6IDAsXG4gIGZjcDogMCxcbiAgdGJ0OiB7XG4gICAgc3RhcnQ6IEluZmluaXR5LFxuICAgIGR1cmF0aW9uOiAwXG4gIH0sXG4gIGNsczoge1xuICAgIHNjb3JlOiAwLFxuICAgIGZpcnN0RW50cnlUaW1lOiBOdW1iZXIuTkVHQVRJVkVfSU5GSU5JVFksXG4gICAgcHJldkVudHJ5VGltZTogTnVtYmVyLk5FR0FUSVZFX0lORklOSVRZLFxuICAgIGN1cnJlbnRTZXNzaW9uU2NvcmU6IDBcbiAgfSxcbiAgbG9uZ3Rhc2s6IHtcbiAgICBjb3VudDogMCxcbiAgICBkdXJhdGlvbjogMCxcbiAgICBtYXg6IDBcbiAgfVxufTtcbnZhciBMT05HX1RBU0tfVEhSRVNIT0xEID0gNTA7XG5leHBvcnQgZnVuY3Rpb24gY3JlYXRlTG9uZ1Rhc2tTcGFucyhsb25ndGFza3MsIGFnZykge1xuICB2YXIgc3BhbnMgPSBbXTtcblxuICBmb3IgKHZhciBpID0gMDsgaSA8IGxvbmd0YXNrcy5sZW5ndGg7IGkrKykge1xuICAgIHZhciBfbG9uZ3Rhc2tzJGkgPSBsb25ndGFza3NbaV0sXG4gICAgICAgIG5hbWUgPSBfbG9uZ3Rhc2tzJGkubmFtZSxcbiAgICAgICAgc3RhcnRUaW1lID0gX2xvbmd0YXNrcyRpLnN0YXJ0VGltZSxcbiAgICAgICAgZHVyYXRpb24gPSBfbG9uZ3Rhc2tzJGkuZHVyYXRpb24sXG4gICAgICAgIGF0dHJpYnV0aW9uID0gX2xvbmd0YXNrcyRpLmF0dHJpYnV0aW9uO1xuICAgIHZhciBlbmQgPSBzdGFydFRpbWUgKyBkdXJhdGlvbjtcbiAgICB2YXIgc3BhbiA9IG5ldyBTcGFuKFwiTG9uZ3Rhc2soXCIgKyBuYW1lICsgXCIpXCIsIExPTkdfVEFTSywge1xuICAgICAgc3RhcnRUaW1lOiBzdGFydFRpbWVcbiAgICB9KTtcbiAgICBhZ2cuY291bnQrKztcbiAgICBhZ2cuZHVyYXRpb24gKz0gZHVyYXRpb247XG4gICAgYWdnLm1heCA9IE1hdGgubWF4KGR1cmF0aW9uLCBhZ2cubWF4KTtcblxuICAgIGlmIChhdHRyaWJ1dGlvbi5sZW5ndGggPiAwKSB7XG4gICAgICB2YXIgX2F0dHJpYnV0aW9uJCA9IGF0dHJpYnV0aW9uWzBdLFxuICAgICAgICAgIF9uYW1lID0gX2F0dHJpYnV0aW9uJC5uYW1lLFxuICAgICAgICAgIGNvbnRhaW5lclR5cGUgPSBfYXR0cmlidXRpb24kLmNvbnRhaW5lclR5cGUsXG4gICAgICAgICAgY29udGFpbmVyTmFtZSA9IF9hdHRyaWJ1dGlvbiQuY29udGFpbmVyTmFtZSxcbiAgICAgICAgICBjb250YWluZXJJZCA9IF9hdHRyaWJ1dGlvbiQuY29udGFpbmVySWQ7XG4gICAgICB2YXIgY3VzdG9tQ29udGV4dCA9IHtcbiAgICAgICAgYXR0cmlidXRpb246IF9uYW1lLFxuICAgICAgICB0eXBlOiBjb250YWluZXJUeXBlXG4gICAgICB9O1xuXG4gICAgICBpZiAoY29udGFpbmVyTmFtZSkge1xuICAgICAgICBjdXN0b21Db250ZXh0Lm5hbWUgPSBjb250YWluZXJOYW1lO1xuICAgICAgfVxuXG4gICAgICBpZiAoY29udGFpbmVySWQpIHtcbiAgICAgICAgY3VzdG9tQ29udGV4dC5pZCA9IGNvbnRhaW5lcklkO1xuICAgICAgfVxuXG4gICAgICBzcGFuLmFkZENvbnRleHQoe1xuICAgICAgICBjdXN0b206IGN1c3RvbUNvbnRleHRcbiAgICAgIH0pO1xuICAgIH1cblxuICAgIHNwYW4uZW5kKGVuZCk7XG4gICAgc3BhbnMucHVzaChzcGFuKTtcbiAgfVxuXG4gIHJldHVybiBzcGFucztcbn1cbmV4cG9ydCBmdW5jdGlvbiBjcmVhdGVGaXJzdElucHV0RGVsYXlTcGFuKGZpZEVudHJpZXMpIHtcbiAgdmFyIGZpcnN0SW5wdXQgPSBmaWRFbnRyaWVzWzBdO1xuXG4gIGlmIChmaXJzdElucHV0KSB7XG4gICAgdmFyIHN0YXJ0VGltZSA9IGZpcnN0SW5wdXQuc3RhcnRUaW1lLFxuICAgICAgICBwcm9jZXNzaW5nU3RhcnQgPSBmaXJzdElucHV0LnByb2Nlc3NpbmdTdGFydDtcbiAgICB2YXIgc3BhbiA9IG5ldyBTcGFuKCdGaXJzdCBJbnB1dCBEZWxheScsIEZJUlNUX0lOUFVULCB7XG4gICAgICBzdGFydFRpbWU6IHN0YXJ0VGltZVxuICAgIH0pO1xuICAgIHNwYW4uZW5kKHByb2Nlc3NpbmdTdGFydCk7XG4gICAgcmV0dXJuIHNwYW47XG4gIH1cbn1cbmV4cG9ydCBmdW5jdGlvbiBjcmVhdGVUb3RhbEJsb2NraW5nVGltZVNwYW4odGJ0T2JqZWN0KSB7XG4gIHZhciBzdGFydCA9IHRidE9iamVjdC5zdGFydCxcbiAgICAgIGR1cmF0aW9uID0gdGJ0T2JqZWN0LmR1cmF0aW9uO1xuICB2YXIgdGJ0U3BhbiA9IG5ldyBTcGFuKCdUb3RhbCBCbG9ja2luZyBUaW1lJywgTE9OR19UQVNLLCB7XG4gICAgc3RhcnRUaW1lOiBzdGFydFxuICB9KTtcbiAgdGJ0U3Bhbi5lbmQoc3RhcnQgKyBkdXJhdGlvbik7XG4gIHJldHVybiB0YnRTcGFuO1xufVxuZXhwb3J0IGZ1bmN0aW9uIGNhbGN1bGF0ZVRvdGFsQmxvY2tpbmdUaW1lKGxvbmd0YXNrRW50cmllcykge1xuICBsb25ndGFza0VudHJpZXMuZm9yRWFjaChmdW5jdGlvbiAoZW50cnkpIHtcbiAgICB2YXIgbmFtZSA9IGVudHJ5Lm5hbWUsXG4gICAgICAgIHN0YXJ0VGltZSA9IGVudHJ5LnN0YXJ0VGltZSxcbiAgICAgICAgZHVyYXRpb24gPSBlbnRyeS5kdXJhdGlvbjtcblxuICAgIGlmIChzdGFydFRpbWUgPCBtZXRyaWNzLmZjcCkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIGlmIChuYW1lICE9PSAnc2VsZicgJiYgbmFtZS5pbmRleE9mKCdzYW1lLW9yaWdpbicpID09PSAtMSkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIG1ldHJpY3MudGJ0LnN0YXJ0ID0gTWF0aC5taW4obWV0cmljcy50YnQuc3RhcnQsIHN0YXJ0VGltZSk7XG4gICAgdmFyIGJsb2NraW5nVGltZSA9IGR1cmF0aW9uIC0gTE9OR19UQVNLX1RIUkVTSE9MRDtcblxuICAgIGlmIChibG9ja2luZ1RpbWUgPiAwKSB7XG4gICAgICBtZXRyaWNzLnRidC5kdXJhdGlvbiArPSBibG9ja2luZ1RpbWU7XG4gICAgfVxuICB9KTtcbn1cbmV4cG9ydCBmdW5jdGlvbiBjYWxjdWxhdGVDdW11bGF0aXZlTGF5b3V0U2hpZnQoY2xzRW50cmllcykge1xuICBjbHNFbnRyaWVzLmZvckVhY2goZnVuY3Rpb24gKGVudHJ5KSB7XG4gICAgaWYgKCFlbnRyeS5oYWRSZWNlbnRJbnB1dCAmJiBlbnRyeS52YWx1ZSkge1xuICAgICAgdmFyIHNob3VsZENyZWF0ZU5ld1Nlc3Npb24gPSBlbnRyeS5zdGFydFRpbWUgLSBtZXRyaWNzLmNscy5maXJzdEVudHJ5VGltZSA+IDUwMDAgfHwgZW50cnkuc3RhcnRUaW1lIC0gbWV0cmljcy5jbHMucHJldkVudHJ5VGltZSA+IDEwMDA7XG5cbiAgICAgIGlmIChzaG91bGRDcmVhdGVOZXdTZXNzaW9uKSB7XG4gICAgICAgIG1ldHJpY3MuY2xzLmZpcnN0RW50cnlUaW1lID0gZW50cnkuc3RhcnRUaW1lO1xuICAgICAgICBtZXRyaWNzLmNscy5jdXJyZW50U2Vzc2lvblNjb3JlID0gMDtcbiAgICAgIH1cblxuICAgICAgbWV0cmljcy5jbHMucHJldkVudHJ5VGltZSA9IGVudHJ5LnN0YXJ0VGltZTtcbiAgICAgIG1ldHJpY3MuY2xzLmN1cnJlbnRTZXNzaW9uU2NvcmUgKz0gZW50cnkudmFsdWU7XG4gICAgICBtZXRyaWNzLmNscy5zY29yZSA9IE1hdGgubWF4KG1ldHJpY3MuY2xzLnNjb3JlLCBtZXRyaWNzLmNscy5jdXJyZW50U2Vzc2lvblNjb3JlKTtcbiAgICB9XG4gIH0pO1xufVxuZXhwb3J0IGZ1bmN0aW9uIGNhcHR1cmVPYnNlcnZlckVudHJpZXMobGlzdCwgX3JlZikge1xuICB2YXIgaXNIYXJkTmF2aWdhdGlvbiA9IF9yZWYuaXNIYXJkTmF2aWdhdGlvbixcbiAgICAgIHRyU3RhcnQgPSBfcmVmLnRyU3RhcnQ7XG4gIHZhciBsb25ndGFza0VudHJpZXMgPSBsaXN0LmdldEVudHJpZXNCeVR5cGUoTE9OR19UQVNLKS5maWx0ZXIoZnVuY3Rpb24gKGVudHJ5KSB7XG4gICAgcmV0dXJuIGVudHJ5LnN0YXJ0VGltZSA+PSB0clN0YXJ0O1xuICB9KTtcbiAgdmFyIGxvbmdUYXNrU3BhbnMgPSBjcmVhdGVMb25nVGFza1NwYW5zKGxvbmd0YXNrRW50cmllcywgbWV0cmljcy5sb25ndGFzayk7XG4gIHZhciByZXN1bHQgPSB7XG4gICAgc3BhbnM6IGxvbmdUYXNrU3BhbnMsXG4gICAgbWFya3M6IHt9XG4gIH07XG5cbiAgaWYgKCFpc0hhcmROYXZpZ2F0aW9uKSB7XG4gICAgcmV0dXJuIHJlc3VsdDtcbiAgfVxuXG4gIHZhciBsY3BFbnRyaWVzID0gbGlzdC5nZXRFbnRyaWVzQnlUeXBlKExBUkdFU1RfQ09OVEVOVEZVTF9QQUlOVCk7XG4gIHZhciBsYXN0TGNwRW50cnkgPSBsY3BFbnRyaWVzW2xjcEVudHJpZXMubGVuZ3RoIC0gMV07XG5cbiAgaWYgKGxhc3RMY3BFbnRyeSkge1xuICAgIHZhciBsY3AgPSBwYXJzZUludChsYXN0TGNwRW50cnkuc3RhcnRUaW1lKTtcbiAgICBtZXRyaWNzLmxjcCA9IGxjcDtcbiAgICByZXN1bHQubWFya3MubGFyZ2VzdENvbnRlbnRmdWxQYWludCA9IGxjcDtcbiAgfVxuXG4gIHZhciB0aW1pbmcgPSBQRVJGLnRpbWluZztcbiAgdmFyIHVubG9hZERpZmYgPSB0aW1pbmcuZmV0Y2hTdGFydCAtIHRpbWluZy5uYXZpZ2F0aW9uU3RhcnQ7XG4gIHZhciBmY3BFbnRyeSA9IGxpc3QuZ2V0RW50cmllc0J5TmFtZShGSVJTVF9DT05URU5URlVMX1BBSU5UKVswXTtcblxuICBpZiAoZmNwRW50cnkpIHtcbiAgICB2YXIgZmNwID0gcGFyc2VJbnQodW5sb2FkRGlmZiA+PSAwID8gZmNwRW50cnkuc3RhcnRUaW1lIC0gdW5sb2FkRGlmZiA6IGZjcEVudHJ5LnN0YXJ0VGltZSk7XG4gICAgbWV0cmljcy5mY3AgPSBmY3A7XG4gICAgcmVzdWx0Lm1hcmtzLmZpcnN0Q29udGVudGZ1bFBhaW50ID0gZmNwO1xuICB9XG5cbiAgdmFyIGZpZEVudHJpZXMgPSBsaXN0LmdldEVudHJpZXNCeVR5cGUoRklSU1RfSU5QVVQpO1xuICB2YXIgZmlkU3BhbiA9IGNyZWF0ZUZpcnN0SW5wdXREZWxheVNwYW4oZmlkRW50cmllcyk7XG5cbiAgaWYgKGZpZFNwYW4pIHtcbiAgICBtZXRyaWNzLmZpZCA9IGZpZFNwYW4uZHVyYXRpb24oKTtcbiAgICByZXN1bHQuc3BhbnMucHVzaChmaWRTcGFuKTtcbiAgfVxuXG4gIGNhbGN1bGF0ZVRvdGFsQmxvY2tpbmdUaW1lKGxvbmd0YXNrRW50cmllcyk7XG4gIHZhciBjbHNFbnRyaWVzID0gbGlzdC5nZXRFbnRyaWVzQnlUeXBlKExBWU9VVF9TSElGVCk7XG4gIGNhbGN1bGF0ZUN1bXVsYXRpdmVMYXlvdXRTaGlmdChjbHNFbnRyaWVzKTtcbiAgcmV0dXJuIHJlc3VsdDtcbn1cbmV4cG9ydCB2YXIgUGVyZkVudHJ5UmVjb3JkZXIgPSBmdW5jdGlvbiAoKSB7XG4gIGZ1bmN0aW9uIFBlcmZFbnRyeVJlY29yZGVyKGNhbGxiYWNrKSB7XG4gICAgdGhpcy5wbyA9IHtcbiAgICAgIG9ic2VydmU6IG5vb3AsXG4gICAgICBkaXNjb25uZWN0OiBub29wXG4gICAgfTtcblxuICAgIGlmICh3aW5kb3cuUGVyZm9ybWFuY2VPYnNlcnZlcikge1xuICAgICAgdGhpcy5wbyA9IG5ldyBQZXJmb3JtYW5jZU9ic2VydmVyKGNhbGxiYWNrKTtcbiAgICB9XG4gIH1cblxuICB2YXIgX3Byb3RvID0gUGVyZkVudHJ5UmVjb3JkZXIucHJvdG90eXBlO1xuXG4gIF9wcm90by5zdGFydCA9IGZ1bmN0aW9uIHN0YXJ0KHR5cGUpIHtcbiAgICB0cnkge1xuICAgICAgdGhpcy5wby5vYnNlcnZlKHtcbiAgICAgICAgdHlwZTogdHlwZSxcbiAgICAgICAgYnVmZmVyZWQ6IHRydWVcbiAgICAgIH0pO1xuICAgIH0gY2F0Y2ggKF8pIHt9XG4gIH07XG5cbiAgX3Byb3RvLnN0b3AgPSBmdW5jdGlvbiBzdG9wKCkge1xuICAgIHRoaXMucG8uZGlzY29ubmVjdCgpO1xuICB9O1xuXG4gIHJldHVybiBQZXJmRW50cnlSZWNvcmRlcjtcbn0oKTsiLCJpbXBvcnQgeyBjaGVja1NhbWVPcmlnaW4sIGlzRHRIZWFkZXJWYWxpZCwgcGFyc2VEdEhlYWRlclZhbHVlLCBnZXREdEhlYWRlclZhbHVlLCBnZXRUU0hlYWRlclZhbHVlLCBzdHJpcFF1ZXJ5U3RyaW5nRnJvbVVybCwgc2V0UmVxdWVzdEhlYWRlciB9IGZyb20gJy4uL2NvbW1vbi91dGlscyc7XG5pbXBvcnQgeyBVcmwgfSBmcm9tICcuLi9jb21tb24vdXJsJztcbmltcG9ydCB7IHBhdGNoRXZlbnRIYW5kbGVyIH0gZnJvbSAnLi4vY29tbW9uL3BhdGNoaW5nJztcbmltcG9ydCB7IGdsb2JhbFN0YXRlIH0gZnJvbSAnLi4vY29tbW9uL3BhdGNoaW5nL3BhdGNoLXV0aWxzJztcbmltcG9ydCB7IFNDSEVEVUxFLCBJTlZPS0UsIFRSQU5TQUNUSU9OX0VORCwgQUZURVJfRVZFTlQsIEZFVENILCBISVNUT1JZLCBYTUxIVFRQUkVRVUVTVCwgSFRUUF9SRVFVRVNUX1RZUEUsIE9VVENPTUVfRkFJTFVSRSwgT1VUQ09NRV9TVUNDRVNTLCBPVVRDT01FX1VOS05PV04sIFFVRVVFX0FERF9UUkFOU0FDVElPTiB9IGZyb20gJy4uL2NvbW1vbi9jb25zdGFudHMnO1xuaW1wb3J0IHsgdHJ1bmNhdGVNb2RlbCwgU1BBTl9NT0RFTCwgVFJBTlNBQ1RJT05fTU9ERUwgfSBmcm9tICcuLi9jb21tb24vdHJ1bmNhdGUnO1xuaW1wb3J0IHsgX19ERVZfXyB9IGZyb20gJy4uL3N0YXRlJztcbnZhciBTSU1JTEFSX1NQQU5fVE9fVFJBTlNBQ1RJT05fUkFUSU8gPSAwLjA1O1xudmFyIFRSQU5TQUNUSU9OX0RVUkFUSU9OX1RIUkVTSE9MRCA9IDYwMDAwO1xuZXhwb3J0IGZ1bmN0aW9uIGdyb3VwU21hbGxDb250aW51b3VzbHlTaW1pbGFyU3BhbnMob3JpZ2luYWxTcGFucywgdHJhbnNEdXJhdGlvbiwgdGhyZXNob2xkKSB7XG4gIG9yaWdpbmFsU3BhbnMuc29ydChmdW5jdGlvbiAoc3BhbkEsIHNwYW5CKSB7XG4gICAgcmV0dXJuIHNwYW5BLl9zdGFydCAtIHNwYW5CLl9zdGFydDtcbiAgfSk7XG4gIHZhciBzcGFucyA9IFtdO1xuICB2YXIgbGFzdENvdW50ID0gMTtcbiAgb3JpZ2luYWxTcGFucy5mb3JFYWNoKGZ1bmN0aW9uIChzcGFuLCBpbmRleCkge1xuICAgIGlmIChzcGFucy5sZW5ndGggPT09IDApIHtcbiAgICAgIHNwYW5zLnB1c2goc3Bhbik7XG4gICAgfSBlbHNlIHtcbiAgICAgIHZhciBsYXN0U3BhbiA9IHNwYW5zW3NwYW5zLmxlbmd0aCAtIDFdO1xuICAgICAgdmFyIGlzQ29udGludW91c2x5U2ltaWxhciA9IGxhc3RTcGFuLnR5cGUgPT09IHNwYW4udHlwZSAmJiBsYXN0U3Bhbi5zdWJ0eXBlID09PSBzcGFuLnN1YnR5cGUgJiYgbGFzdFNwYW4uYWN0aW9uID09PSBzcGFuLmFjdGlvbiAmJiBsYXN0U3Bhbi5uYW1lID09PSBzcGFuLm5hbWUgJiYgc3Bhbi5kdXJhdGlvbigpIC8gdHJhbnNEdXJhdGlvbiA8IHRocmVzaG9sZCAmJiAoc3Bhbi5fc3RhcnQgLSBsYXN0U3Bhbi5fZW5kKSAvIHRyYW5zRHVyYXRpb24gPCB0aHJlc2hvbGQ7XG4gICAgICB2YXIgaXNMYXN0U3BhbiA9IG9yaWdpbmFsU3BhbnMubGVuZ3RoID09PSBpbmRleCArIDE7XG5cbiAgICAgIGlmIChpc0NvbnRpbnVvdXNseVNpbWlsYXIpIHtcbiAgICAgICAgbGFzdENvdW50Kys7XG4gICAgICAgIGxhc3RTcGFuLl9lbmQgPSBzcGFuLl9lbmQ7XG4gICAgICB9XG5cbiAgICAgIGlmIChsYXN0Q291bnQgPiAxICYmICghaXNDb250aW51b3VzbHlTaW1pbGFyIHx8IGlzTGFzdFNwYW4pKSB7XG4gICAgICAgIGxhc3RTcGFuLm5hbWUgPSBsYXN0Q291bnQgKyAneCAnICsgbGFzdFNwYW4ubmFtZTtcbiAgICAgICAgbGFzdENvdW50ID0gMTtcbiAgICAgIH1cblxuICAgICAgaWYgKCFpc0NvbnRpbnVvdXNseVNpbWlsYXIpIHtcbiAgICAgICAgc3BhbnMucHVzaChzcGFuKTtcbiAgICAgIH1cbiAgICB9XG4gIH0pO1xuICByZXR1cm4gc3BhbnM7XG59XG5leHBvcnQgZnVuY3Rpb24gYWRqdXN0VHJhbnNhY3Rpb24odHJhbnNhY3Rpb24pIHtcbiAgaWYgKHRyYW5zYWN0aW9uLnNhbXBsZWQpIHtcbiAgICB2YXIgZmlsdGVyZFNwYW5zID0gdHJhbnNhY3Rpb24uc3BhbnMuZmlsdGVyKGZ1bmN0aW9uIChzcGFuKSB7XG4gICAgICByZXR1cm4gc3Bhbi5kdXJhdGlvbigpID4gMCAmJiBzcGFuLl9zdGFydCA+PSB0cmFuc2FjdGlvbi5fc3RhcnQgJiYgc3Bhbi5fZW5kIDw9IHRyYW5zYWN0aW9uLl9lbmQ7XG4gICAgfSk7XG5cbiAgICBpZiAodHJhbnNhY3Rpb24uaXNNYW5hZ2VkKCkpIHtcbiAgICAgIHZhciBkdXJhdGlvbiA9IHRyYW5zYWN0aW9uLmR1cmF0aW9uKCk7XG4gICAgICB2YXIgc2ltaWxhclNwYW5zID0gZ3JvdXBTbWFsbENvbnRpbnVvdXNseVNpbWlsYXJTcGFucyhmaWx0ZXJkU3BhbnMsIGR1cmF0aW9uLCBTSU1JTEFSX1NQQU5fVE9fVFJBTlNBQ1RJT05fUkFUSU8pO1xuICAgICAgdHJhbnNhY3Rpb24uc3BhbnMgPSBzaW1pbGFyU3BhbnM7XG4gICAgfSBlbHNlIHtcbiAgICAgIHRyYW5zYWN0aW9uLnNwYW5zID0gZmlsdGVyZFNwYW5zO1xuICAgIH1cbiAgfSBlbHNlIHtcbiAgICB0cmFuc2FjdGlvbi5yZXNldEZpZWxkcygpO1xuICB9XG5cbiAgcmV0dXJuIHRyYW5zYWN0aW9uO1xufVxuXG52YXIgUGVyZm9ybWFuY2VNb25pdG9yaW5nID0gZnVuY3Rpb24gKCkge1xuICBmdW5jdGlvbiBQZXJmb3JtYW5jZU1vbml0b3JpbmcoYXBtU2VydmVyLCBjb25maWdTZXJ2aWNlLCBsb2dnaW5nU2VydmljZSwgdHJhbnNhY3Rpb25TZXJ2aWNlKSB7XG4gICAgdGhpcy5fYXBtU2VydmVyID0gYXBtU2VydmVyO1xuICAgIHRoaXMuX2NvbmZpZ1NlcnZpY2UgPSBjb25maWdTZXJ2aWNlO1xuICAgIHRoaXMuX2xvZ2dpblNlcnZpY2UgPSBsb2dnaW5nU2VydmljZTtcbiAgICB0aGlzLl90cmFuc2FjdGlvblNlcnZpY2UgPSB0cmFuc2FjdGlvblNlcnZpY2U7XG4gIH1cblxuICB2YXIgX3Byb3RvID0gUGVyZm9ybWFuY2VNb25pdG9yaW5nLnByb3RvdHlwZTtcblxuICBfcHJvdG8uaW5pdCA9IGZ1bmN0aW9uIGluaXQoZmxhZ3MpIHtcbiAgICB2YXIgX3RoaXMgPSB0aGlzO1xuXG4gICAgaWYgKGZsYWdzID09PSB2b2lkIDApIHtcbiAgICAgIGZsYWdzID0ge307XG4gICAgfVxuXG4gICAgdGhpcy5fY29uZmlnU2VydmljZS5ldmVudHMub2JzZXJ2ZShUUkFOU0FDVElPTl9FTkQgKyBBRlRFUl9FVkVOVCwgZnVuY3Rpb24gKHRyKSB7XG4gICAgICB2YXIgcGF5bG9hZCA9IF90aGlzLmNyZWF0ZVRyYW5zYWN0aW9uUGF5bG9hZCh0cik7XG5cbiAgICAgIGlmIChwYXlsb2FkKSB7XG4gICAgICAgIF90aGlzLl9hcG1TZXJ2ZXIuYWRkVHJhbnNhY3Rpb24ocGF5bG9hZCk7XG5cbiAgICAgICAgX3RoaXMuX2NvbmZpZ1NlcnZpY2UuZGlzcGF0Y2hFdmVudChRVUVVRV9BRERfVFJBTlNBQ1RJT04pO1xuICAgICAgfVxuICAgIH0pO1xuXG4gICAgaWYgKGZsYWdzW0hJU1RPUlldKSB7XG4gICAgICBwYXRjaEV2ZW50SGFuZGxlci5vYnNlcnZlKEhJU1RPUlksIHRoaXMuZ2V0SGlzdG9yeVN1YigpKTtcbiAgICB9XG5cbiAgICBpZiAoZmxhZ3NbWE1MSFRUUFJFUVVFU1RdKSB7XG4gICAgICBwYXRjaEV2ZW50SGFuZGxlci5vYnNlcnZlKFhNTEhUVFBSRVFVRVNULCB0aGlzLmdldFhIUlN1YigpKTtcbiAgICB9XG5cbiAgICBpZiAoZmxhZ3NbRkVUQ0hdKSB7XG4gICAgICBwYXRjaEV2ZW50SGFuZGxlci5vYnNlcnZlKEZFVENILCB0aGlzLmdldEZldGNoU3ViKCkpO1xuICAgIH1cbiAgfTtcblxuICBfcHJvdG8uZ2V0SGlzdG9yeVN1YiA9IGZ1bmN0aW9uIGdldEhpc3RvcnlTdWIoKSB7XG4gICAgdmFyIHRyYW5zYWN0aW9uU2VydmljZSA9IHRoaXMuX3RyYW5zYWN0aW9uU2VydmljZTtcbiAgICByZXR1cm4gZnVuY3Rpb24gKGV2ZW50LCB0YXNrKSB7XG4gICAgICBpZiAodGFzay5zb3VyY2UgPT09IEhJU1RPUlkgJiYgZXZlbnQgPT09IElOVk9LRSkge1xuICAgICAgICB0cmFuc2FjdGlvblNlcnZpY2Uuc3RhcnRUcmFuc2FjdGlvbih0YXNrLmRhdGEudGl0bGUsICdyb3V0ZS1jaGFuZ2UnLCB7XG4gICAgICAgICAgbWFuYWdlZDogdHJ1ZSxcbiAgICAgICAgICBjYW5SZXVzZTogdHJ1ZVxuICAgICAgICB9KTtcbiAgICAgIH1cbiAgICB9O1xuICB9O1xuXG4gIF9wcm90by5nZXRYSFJTdWIgPSBmdW5jdGlvbiBnZXRYSFJTdWIoKSB7XG4gICAgdmFyIF90aGlzMiA9IHRoaXM7XG5cbiAgICByZXR1cm4gZnVuY3Rpb24gKGV2ZW50LCB0YXNrKSB7XG4gICAgICBpZiAodGFzay5zb3VyY2UgPT09IFhNTEhUVFBSRVFVRVNUICYmICFnbG9iYWxTdGF0ZS5mZXRjaEluUHJvZ3Jlc3MpIHtcbiAgICAgICAgX3RoaXMyLnByb2Nlc3NBUElDYWxscyhldmVudCwgdGFzayk7XG4gICAgICB9XG4gICAgfTtcbiAgfTtcblxuICBfcHJvdG8uZ2V0RmV0Y2hTdWIgPSBmdW5jdGlvbiBnZXRGZXRjaFN1YigpIHtcbiAgICB2YXIgX3RoaXMzID0gdGhpcztcblxuICAgIHJldHVybiBmdW5jdGlvbiAoZXZlbnQsIHRhc2spIHtcbiAgICAgIGlmICh0YXNrLnNvdXJjZSA9PT0gRkVUQ0gpIHtcbiAgICAgICAgX3RoaXMzLnByb2Nlc3NBUElDYWxscyhldmVudCwgdGFzayk7XG4gICAgICB9XG4gICAgfTtcbiAgfTtcblxuICBfcHJvdG8ucHJvY2Vzc0FQSUNhbGxzID0gZnVuY3Rpb24gcHJvY2Vzc0FQSUNhbGxzKGV2ZW50LCB0YXNrKSB7XG4gICAgdmFyIGNvbmZpZ1NlcnZpY2UgPSB0aGlzLl9jb25maWdTZXJ2aWNlO1xuICAgIHZhciB0cmFuc2FjdGlvblNlcnZpY2UgPSB0aGlzLl90cmFuc2FjdGlvblNlcnZpY2U7XG5cbiAgICBpZiAodGFzay5kYXRhICYmIHRhc2suZGF0YS51cmwpIHtcbiAgICAgIHZhciBlbmRwb2ludHMgPSB0aGlzLl9hcG1TZXJ2ZXIuZ2V0RW5kcG9pbnRzKCk7XG5cbiAgICAgIHZhciBpc093bkVuZHBvaW50ID0gT2JqZWN0LmtleXMoZW5kcG9pbnRzKS5zb21lKGZ1bmN0aW9uIChlbmRwb2ludCkge1xuICAgICAgICByZXR1cm4gdGFzay5kYXRhLnVybC5pbmRleE9mKGVuZHBvaW50c1tlbmRwb2ludF0pICE9PSAtMTtcbiAgICAgIH0pO1xuXG4gICAgICBpZiAoaXNPd25FbmRwb2ludCkge1xuICAgICAgICByZXR1cm47XG4gICAgICB9XG4gICAgfVxuXG4gICAgaWYgKGV2ZW50ID09PSBTQ0hFRFVMRSAmJiB0YXNrLmRhdGEpIHtcbiAgICAgIHZhciBkYXRhID0gdGFzay5kYXRhO1xuICAgICAgdmFyIHJlcXVlc3RVcmwgPSBuZXcgVXJsKGRhdGEudXJsKTtcbiAgICAgIHZhciBzcGFuTmFtZSA9IGRhdGEubWV0aG9kICsgJyAnICsgKHJlcXVlc3RVcmwucmVsYXRpdmUgPyByZXF1ZXN0VXJsLnBhdGggOiBzdHJpcFF1ZXJ5U3RyaW5nRnJvbVVybChyZXF1ZXN0VXJsLmhyZWYpKTtcblxuICAgICAgaWYgKCF0cmFuc2FjdGlvblNlcnZpY2UuZ2V0Q3VycmVudFRyYW5zYWN0aW9uKCkpIHtcbiAgICAgICAgdHJhbnNhY3Rpb25TZXJ2aWNlLnN0YXJ0VHJhbnNhY3Rpb24oc3Bhbk5hbWUsIEhUVFBfUkVRVUVTVF9UWVBFLCB7XG4gICAgICAgICAgbWFuYWdlZDogdHJ1ZVxuICAgICAgICB9KTtcbiAgICAgIH1cblxuICAgICAgdmFyIHNwYW4gPSB0cmFuc2FjdGlvblNlcnZpY2Uuc3RhcnRTcGFuKHNwYW5OYW1lLCAnZXh0ZXJuYWwuaHR0cCcsIHtcbiAgICAgICAgYmxvY2tpbmc6IHRydWVcbiAgICAgIH0pO1xuXG4gICAgICBpZiAoIXNwYW4pIHtcbiAgICAgICAgcmV0dXJuO1xuICAgICAgfVxuXG4gICAgICB2YXIgaXNEdEVuYWJsZWQgPSBjb25maWdTZXJ2aWNlLmdldCgnZGlzdHJpYnV0ZWRUcmFjaW5nJyk7XG4gICAgICB2YXIgZHRPcmlnaW5zID0gY29uZmlnU2VydmljZS5nZXQoJ2Rpc3RyaWJ1dGVkVHJhY2luZ09yaWdpbnMnKTtcbiAgICAgIHZhciBjdXJyZW50VXJsID0gbmV3IFVybCh3aW5kb3cubG9jYXRpb24uaHJlZik7XG4gICAgICB2YXIgaXNTYW1lT3JpZ2luID0gY2hlY2tTYW1lT3JpZ2luKHJlcXVlc3RVcmwub3JpZ2luLCBjdXJyZW50VXJsLm9yaWdpbikgfHwgY2hlY2tTYW1lT3JpZ2luKHJlcXVlc3RVcmwub3JpZ2luLCBkdE9yaWdpbnMpO1xuICAgICAgdmFyIHRhcmdldCA9IGRhdGEudGFyZ2V0O1xuXG4gICAgICBpZiAoaXNEdEVuYWJsZWQgJiYgaXNTYW1lT3JpZ2luICYmIHRhcmdldCkge1xuICAgICAgICB0aGlzLmluamVjdER0SGVhZGVyKHNwYW4sIHRhcmdldCk7XG4gICAgICAgIHZhciBwcm9wYWdhdGVUcmFjZXN0YXRlID0gY29uZmlnU2VydmljZS5nZXQoJ3Byb3BhZ2F0ZVRyYWNlc3RhdGUnKTtcblxuICAgICAgICBpZiAocHJvcGFnYXRlVHJhY2VzdGF0ZSkge1xuICAgICAgICAgIHRoaXMuaW5qZWN0VFNIZWFkZXIoc3BhbiwgdGFyZ2V0KTtcbiAgICAgICAgfVxuICAgICAgfSBlbHNlIGlmIChfX0RFVl9fKSB7XG4gICAgICAgIHRoaXMuX2xvZ2dpblNlcnZpY2UuZGVidWcoXCJDb3VsZCBub3QgaW5qZWN0IGRpc3RyaWJ1dGVkIHRyYWNpbmcgaGVhZGVyIHRvIHRoZSByZXF1ZXN0IG9yaWdpbiAoJ1wiICsgcmVxdWVzdFVybC5vcmlnaW4gKyBcIicpIGZyb20gdGhlIGN1cnJlbnQgb3JpZ2luICgnXCIgKyBjdXJyZW50VXJsLm9yaWdpbiArIFwiJylcIik7XG4gICAgICB9XG5cbiAgICAgIGlmIChkYXRhLnN5bmMpIHtcbiAgICAgICAgc3Bhbi5zeW5jID0gZGF0YS5zeW5jO1xuICAgICAgfVxuXG4gICAgICBkYXRhLnNwYW4gPSBzcGFuO1xuICAgIH0gZWxzZSBpZiAoZXZlbnQgPT09IElOVk9LRSkge1xuICAgICAgdmFyIF9kYXRhID0gdGFzay5kYXRhO1xuXG4gICAgICBpZiAoX2RhdGEgJiYgX2RhdGEuc3Bhbikge1xuICAgICAgICB2YXIgX3NwYW4gPSBfZGF0YS5zcGFuLFxuICAgICAgICAgICAgcmVzcG9uc2UgPSBfZGF0YS5yZXNwb25zZSxcbiAgICAgICAgICAgIF90YXJnZXQgPSBfZGF0YS50YXJnZXQ7XG4gICAgICAgIHZhciBzdGF0dXM7XG5cbiAgICAgICAgaWYgKHJlc3BvbnNlKSB7XG4gICAgICAgICAgc3RhdHVzID0gcmVzcG9uc2Uuc3RhdHVzO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgIHN0YXR1cyA9IF90YXJnZXQuc3RhdHVzO1xuICAgICAgICB9XG5cbiAgICAgICAgdmFyIG91dGNvbWU7XG5cbiAgICAgICAgaWYgKF9kYXRhLnN0YXR1cyAhPSAnYWJvcnQnICYmICFfZGF0YS5hYm9ydGVkKSB7XG4gICAgICAgICAgaWYgKHN0YXR1cyA+PSA0MDAgfHwgc3RhdHVzID09IDApIHtcbiAgICAgICAgICAgIG91dGNvbWUgPSBPVVRDT01FX0ZBSUxVUkU7XG4gICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgIG91dGNvbWUgPSBPVVRDT01FX1NVQ0NFU1M7XG4gICAgICAgICAgfVxuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgIG91dGNvbWUgPSBPVVRDT01FX1VOS05PV047XG4gICAgICAgIH1cblxuICAgICAgICBfc3Bhbi5vdXRjb21lID0gb3V0Y29tZTtcbiAgICAgICAgdmFyIHRyID0gdHJhbnNhY3Rpb25TZXJ2aWNlLmdldEN1cnJlbnRUcmFuc2FjdGlvbigpO1xuXG4gICAgICAgIGlmICh0ciAmJiB0ci50eXBlID09PSBIVFRQX1JFUVVFU1RfVFlQRSkge1xuICAgICAgICAgIHRyLm91dGNvbWUgPSBvdXRjb21lO1xuICAgICAgICB9XG5cbiAgICAgICAgdHJhbnNhY3Rpb25TZXJ2aWNlLmVuZFNwYW4oX3NwYW4sIF9kYXRhKTtcbiAgICAgIH1cbiAgICB9XG4gIH07XG5cbiAgX3Byb3RvLmluamVjdER0SGVhZGVyID0gZnVuY3Rpb24gaW5qZWN0RHRIZWFkZXIoc3BhbiwgdGFyZ2V0KSB7XG4gICAgdmFyIGhlYWRlck5hbWUgPSB0aGlzLl9jb25maWdTZXJ2aWNlLmdldCgnZGlzdHJpYnV0ZWRUcmFjaW5nSGVhZGVyTmFtZScpO1xuXG4gICAgdmFyIGhlYWRlclZhbHVlID0gZ2V0RHRIZWFkZXJWYWx1ZShzcGFuKTtcbiAgICB2YXIgaXNIZWFkZXJWYWxpZCA9IGlzRHRIZWFkZXJWYWxpZChoZWFkZXJWYWx1ZSk7XG5cbiAgICBpZiAoaXNIZWFkZXJWYWxpZCAmJiBoZWFkZXJWYWx1ZSAmJiBoZWFkZXJOYW1lKSB7XG4gICAgICBzZXRSZXF1ZXN0SGVhZGVyKHRhcmdldCwgaGVhZGVyTmFtZSwgaGVhZGVyVmFsdWUpO1xuICAgIH1cbiAgfTtcblxuICBfcHJvdG8uaW5qZWN0VFNIZWFkZXIgPSBmdW5jdGlvbiBpbmplY3RUU0hlYWRlcihzcGFuLCB0YXJnZXQpIHtcbiAgICB2YXIgaGVhZGVyVmFsdWUgPSBnZXRUU0hlYWRlclZhbHVlKHNwYW4pO1xuXG4gICAgaWYgKGhlYWRlclZhbHVlKSB7XG4gICAgICBzZXRSZXF1ZXN0SGVhZGVyKHRhcmdldCwgJ3RyYWNlc3RhdGUnLCBoZWFkZXJWYWx1ZSk7XG4gICAgfVxuICB9O1xuXG4gIF9wcm90by5leHRyYWN0RHRIZWFkZXIgPSBmdW5jdGlvbiBleHRyYWN0RHRIZWFkZXIodGFyZ2V0KSB7XG4gICAgdmFyIGNvbmZpZ1NlcnZpY2UgPSB0aGlzLl9jb25maWdTZXJ2aWNlO1xuICAgIHZhciBoZWFkZXJOYW1lID0gY29uZmlnU2VydmljZS5nZXQoJ2Rpc3RyaWJ1dGVkVHJhY2luZ0hlYWRlck5hbWUnKTtcblxuICAgIGlmICh0YXJnZXQpIHtcbiAgICAgIHJldHVybiBwYXJzZUR0SGVhZGVyVmFsdWUodGFyZ2V0W2hlYWRlck5hbWVdKTtcbiAgICB9XG4gIH07XG5cbiAgX3Byb3RvLmZpbHRlclRyYW5zYWN0aW9uID0gZnVuY3Rpb24gZmlsdGVyVHJhbnNhY3Rpb24odHIpIHtcbiAgICB2YXIgZHVyYXRpb24gPSB0ci5kdXJhdGlvbigpO1xuXG4gICAgaWYgKCFkdXJhdGlvbikge1xuICAgICAgaWYgKF9fREVWX18pIHtcbiAgICAgICAgdmFyIG1lc3NhZ2UgPSBcInRyYW5zYWN0aW9uKFwiICsgdHIuaWQgKyBcIiwgXCIgKyB0ci5uYW1lICsgXCIpIHdhcyBkaXNjYXJkZWQhIFwiO1xuXG4gICAgICAgIGlmIChkdXJhdGlvbiA9PT0gMCkge1xuICAgICAgICAgIG1lc3NhZ2UgKz0gXCJUcmFuc2FjdGlvbiBkdXJhdGlvbiBpcyAwXCI7XG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgbWVzc2FnZSArPSBcIlRyYW5zYWN0aW9uIHdhc24ndCBlbmRlZFwiO1xuICAgICAgICB9XG5cbiAgICAgICAgdGhpcy5fbG9nZ2luU2VydmljZS5kZWJ1ZyhtZXNzYWdlKTtcbiAgICAgIH1cblxuICAgICAgcmV0dXJuIGZhbHNlO1xuICAgIH1cblxuICAgIGlmICh0ci5pc01hbmFnZWQoKSkge1xuICAgICAgaWYgKGR1cmF0aW9uID4gVFJBTlNBQ1RJT05fRFVSQVRJT05fVEhSRVNIT0xEKSB7XG4gICAgICAgIGlmIChfX0RFVl9fKSB7XG4gICAgICAgICAgdGhpcy5fbG9nZ2luU2VydmljZS5kZWJ1ZyhcInRyYW5zYWN0aW9uKFwiICsgdHIuaWQgKyBcIiwgXCIgKyB0ci5uYW1lICsgXCIpIHdhcyBkaXNjYXJkZWQhIFRyYW5zYWN0aW9uIGR1cmF0aW9uIChcIiArIGR1cmF0aW9uICsgXCIpIGlzIGdyZWF0ZXIgdGhhbiBtYW5hZ2VkIHRyYW5zYWN0aW9uIHRocmVzaG9sZCAoXCIgKyBUUkFOU0FDVElPTl9EVVJBVElPTl9USFJFU0hPTEQgKyBcIilcIik7XG4gICAgICAgIH1cblxuICAgICAgICByZXR1cm4gZmFsc2U7XG4gICAgICB9XG5cbiAgICAgIGlmICh0ci5zYW1wbGVkICYmIHRyLnNwYW5zLmxlbmd0aCA9PT0gMCkge1xuICAgICAgICBpZiAoX19ERVZfXykge1xuICAgICAgICAgIHRoaXMuX2xvZ2dpblNlcnZpY2UuZGVidWcoXCJ0cmFuc2FjdGlvbihcIiArIHRyLmlkICsgXCIsIFwiICsgdHIubmFtZSArIFwiKSB3YXMgZGlzY2FyZGVkISBUcmFuc2FjdGlvbiBkb2VzIG5vdCBoYXZlIGFueSBzcGFuc1wiKTtcbiAgICAgICAgfVxuXG4gICAgICAgIHJldHVybiBmYWxzZTtcbiAgICAgIH1cbiAgICB9XG5cbiAgICByZXR1cm4gdHJ1ZTtcbiAgfTtcblxuICBfcHJvdG8uY3JlYXRlVHJhbnNhY3Rpb25EYXRhTW9kZWwgPSBmdW5jdGlvbiBjcmVhdGVUcmFuc2FjdGlvbkRhdGFNb2RlbCh0cmFuc2FjdGlvbikge1xuICAgIHZhciB0cmFuc2FjdGlvblN0YXJ0ID0gdHJhbnNhY3Rpb24uX3N0YXJ0O1xuICAgIHZhciBzcGFucyA9IHRyYW5zYWN0aW9uLnNwYW5zLm1hcChmdW5jdGlvbiAoc3Bhbikge1xuICAgICAgdmFyIHNwYW5EYXRhID0ge1xuICAgICAgICBpZDogc3Bhbi5pZCxcbiAgICAgICAgdHJhbnNhY3Rpb25faWQ6IHRyYW5zYWN0aW9uLmlkLFxuICAgICAgICBwYXJlbnRfaWQ6IHNwYW4ucGFyZW50SWQgfHwgdHJhbnNhY3Rpb24uaWQsXG4gICAgICAgIHRyYWNlX2lkOiB0cmFuc2FjdGlvbi50cmFjZUlkLFxuICAgICAgICBuYW1lOiBzcGFuLm5hbWUsXG4gICAgICAgIHR5cGU6IHNwYW4udHlwZSxcbiAgICAgICAgc3VidHlwZTogc3Bhbi5zdWJ0eXBlLFxuICAgICAgICBhY3Rpb246IHNwYW4uYWN0aW9uLFxuICAgICAgICBzeW5jOiBzcGFuLnN5bmMsXG4gICAgICAgIHN0YXJ0OiBwYXJzZUludChzcGFuLl9zdGFydCAtIHRyYW5zYWN0aW9uU3RhcnQpLFxuICAgICAgICBkdXJhdGlvbjogc3Bhbi5kdXJhdGlvbigpLFxuICAgICAgICBjb250ZXh0OiBzcGFuLmNvbnRleHQsXG4gICAgICAgIG91dGNvbWU6IHNwYW4ub3V0Y29tZSxcbiAgICAgICAgc2FtcGxlX3JhdGU6IHNwYW4uc2FtcGxlUmF0ZVxuICAgICAgfTtcbiAgICAgIHJldHVybiB0cnVuY2F0ZU1vZGVsKFNQQU5fTU9ERUwsIHNwYW5EYXRhKTtcbiAgICB9KTtcbiAgICB2YXIgdHJhbnNhY3Rpb25EYXRhID0ge1xuICAgICAgaWQ6IHRyYW5zYWN0aW9uLmlkLFxuICAgICAgdHJhY2VfaWQ6IHRyYW5zYWN0aW9uLnRyYWNlSWQsXG4gICAgICBzZXNzaW9uOiB0cmFuc2FjdGlvbi5zZXNzaW9uLFxuICAgICAgbmFtZTogdHJhbnNhY3Rpb24ubmFtZSxcbiAgICAgIHR5cGU6IHRyYW5zYWN0aW9uLnR5cGUsXG4gICAgICBkdXJhdGlvbjogdHJhbnNhY3Rpb24uZHVyYXRpb24oKSxcbiAgICAgIHNwYW5zOiBzcGFucyxcbiAgICAgIGNvbnRleHQ6IHRyYW5zYWN0aW9uLmNvbnRleHQsXG4gICAgICBtYXJrczogdHJhbnNhY3Rpb24ubWFya3MsXG4gICAgICBicmVha2Rvd246IHRyYW5zYWN0aW9uLmJyZWFrZG93blRpbWluZ3MsXG4gICAgICBzcGFuX2NvdW50OiB7XG4gICAgICAgIHN0YXJ0ZWQ6IHNwYW5zLmxlbmd0aFxuICAgICAgfSxcbiAgICAgIHNhbXBsZWQ6IHRyYW5zYWN0aW9uLnNhbXBsZWQsXG4gICAgICBzYW1wbGVfcmF0ZTogdHJhbnNhY3Rpb24uc2FtcGxlUmF0ZSxcbiAgICAgIGV4cGVyaWVuY2U6IHRyYW5zYWN0aW9uLmV4cGVyaWVuY2UsXG4gICAgICBvdXRjb21lOiB0cmFuc2FjdGlvbi5vdXRjb21lXG4gICAgfTtcbiAgICByZXR1cm4gdHJ1bmNhdGVNb2RlbChUUkFOU0FDVElPTl9NT0RFTCwgdHJhbnNhY3Rpb25EYXRhKTtcbiAgfTtcblxuICBfcHJvdG8uY3JlYXRlVHJhbnNhY3Rpb25QYXlsb2FkID0gZnVuY3Rpb24gY3JlYXRlVHJhbnNhY3Rpb25QYXlsb2FkKHRyYW5zYWN0aW9uKSB7XG4gICAgdmFyIGFkanVzdGVkVHJhbnNhY3Rpb24gPSBhZGp1c3RUcmFuc2FjdGlvbih0cmFuc2FjdGlvbik7XG4gICAgdmFyIGZpbHRlcmVkID0gdGhpcy5maWx0ZXJUcmFuc2FjdGlvbihhZGp1c3RlZFRyYW5zYWN0aW9uKTtcblxuICAgIGlmIChmaWx0ZXJlZCkge1xuICAgICAgcmV0dXJuIHRoaXMuY3JlYXRlVHJhbnNhY3Rpb25EYXRhTW9kZWwodHJhbnNhY3Rpb24pO1xuICAgIH1cbiAgfTtcblxuICByZXR1cm4gUGVyZm9ybWFuY2VNb25pdG9yaW5nO1xufSgpO1xuXG5leHBvcnQgeyBQZXJmb3JtYW5jZU1vbml0b3JpbmcgYXMgZGVmYXVsdCB9OyIsImltcG9ydCB7IGdlbmVyYXRlUmFuZG9tSWQsIHNldExhYmVsLCBtZXJnZSwgZ2V0RHVyYXRpb24sIGdldFRpbWUgfSBmcm9tICcuLi9jb21tb24vdXRpbHMnO1xuaW1wb3J0IHsgTkFNRV9VTktOT1dOLCBUWVBFX0NVU1RPTSB9IGZyb20gJy4uL2NvbW1vbi9jb25zdGFudHMnO1xuXG52YXIgU3BhbkJhc2UgPSBmdW5jdGlvbiAoKSB7XG4gIGZ1bmN0aW9uIFNwYW5CYXNlKG5hbWUsIHR5cGUsIG9wdGlvbnMpIHtcbiAgICBpZiAob3B0aW9ucyA9PT0gdm9pZCAwKSB7XG4gICAgICBvcHRpb25zID0ge307XG4gICAgfVxuXG4gICAgaWYgKCFuYW1lKSB7XG4gICAgICBuYW1lID0gTkFNRV9VTktOT1dOO1xuICAgIH1cblxuICAgIGlmICghdHlwZSkge1xuICAgICAgdHlwZSA9IFRZUEVfQ1VTVE9NO1xuICAgIH1cblxuICAgIHRoaXMubmFtZSA9IG5hbWU7XG4gICAgdGhpcy50eXBlID0gdHlwZTtcbiAgICB0aGlzLm9wdGlvbnMgPSBvcHRpb25zO1xuICAgIHRoaXMuaWQgPSBvcHRpb25zLmlkIHx8IGdlbmVyYXRlUmFuZG9tSWQoMTYpO1xuICAgIHRoaXMudHJhY2VJZCA9IG9wdGlvbnMudHJhY2VJZDtcbiAgICB0aGlzLnNhbXBsZWQgPSBvcHRpb25zLnNhbXBsZWQ7XG4gICAgdGhpcy5zYW1wbGVSYXRlID0gb3B0aW9ucy5zYW1wbGVSYXRlO1xuICAgIHRoaXMudGltZXN0YW1wID0gb3B0aW9ucy50aW1lc3RhbXA7XG4gICAgdGhpcy5fc3RhcnQgPSBnZXRUaW1lKG9wdGlvbnMuc3RhcnRUaW1lKTtcbiAgICB0aGlzLl9lbmQgPSB1bmRlZmluZWQ7XG4gICAgdGhpcy5lbmRlZCA9IGZhbHNlO1xuICAgIHRoaXMub3V0Y29tZSA9IHVuZGVmaW5lZDtcbiAgICB0aGlzLm9uRW5kID0gb3B0aW9ucy5vbkVuZDtcbiAgfVxuXG4gIHZhciBfcHJvdG8gPSBTcGFuQmFzZS5wcm90b3R5cGU7XG5cbiAgX3Byb3RvLmVuc3VyZUNvbnRleHQgPSBmdW5jdGlvbiBlbnN1cmVDb250ZXh0KCkge1xuICAgIGlmICghdGhpcy5jb250ZXh0KSB7XG4gICAgICB0aGlzLmNvbnRleHQgPSB7fTtcbiAgICB9XG4gIH07XG5cbiAgX3Byb3RvLmFkZExhYmVscyA9IGZ1bmN0aW9uIGFkZExhYmVscyh0YWdzKSB7XG4gICAgdGhpcy5lbnN1cmVDb250ZXh0KCk7XG4gICAgdmFyIGN0eCA9IHRoaXMuY29udGV4dDtcblxuICAgIGlmICghY3R4LnRhZ3MpIHtcbiAgICAgIGN0eC50YWdzID0ge307XG4gICAgfVxuXG4gICAgdmFyIGtleXMgPSBPYmplY3Qua2V5cyh0YWdzKTtcbiAgICBrZXlzLmZvckVhY2goZnVuY3Rpb24gKGspIHtcbiAgICAgIHJldHVybiBzZXRMYWJlbChrLCB0YWdzW2tdLCBjdHgudGFncyk7XG4gICAgfSk7XG4gIH07XG5cbiAgX3Byb3RvLmFkZENvbnRleHQgPSBmdW5jdGlvbiBhZGRDb250ZXh0KCkge1xuICAgIGZvciAodmFyIF9sZW4gPSBhcmd1bWVudHMubGVuZ3RoLCBjb250ZXh0ID0gbmV3IEFycmF5KF9sZW4pLCBfa2V5ID0gMDsgX2tleSA8IF9sZW47IF9rZXkrKykge1xuICAgICAgY29udGV4dFtfa2V5XSA9IGFyZ3VtZW50c1tfa2V5XTtcbiAgICB9XG5cbiAgICBpZiAoY29udGV4dC5sZW5ndGggPT09IDApIHJldHVybjtcbiAgICB0aGlzLmVuc3VyZUNvbnRleHQoKTtcbiAgICBtZXJnZS5hcHBseSh2b2lkIDAsIFt0aGlzLmNvbnRleHRdLmNvbmNhdChjb250ZXh0KSk7XG4gIH07XG5cbiAgX3Byb3RvLmVuZCA9IGZ1bmN0aW9uIGVuZChlbmRUaW1lKSB7XG4gICAgaWYgKHRoaXMuZW5kZWQpIHtcbiAgICAgIHJldHVybjtcbiAgICB9XG5cbiAgICB0aGlzLmVuZGVkID0gdHJ1ZTtcbiAgICB0aGlzLl9lbmQgPSBnZXRUaW1lKGVuZFRpbWUpO1xuICAgIHRoaXMuY2FsbE9uRW5kKCk7XG4gIH07XG5cbiAgX3Byb3RvLmNhbGxPbkVuZCA9IGZ1bmN0aW9uIGNhbGxPbkVuZCgpIHtcbiAgICBpZiAodHlwZW9mIHRoaXMub25FbmQgPT09ICdmdW5jdGlvbicpIHtcbiAgICAgIHRoaXMub25FbmQodGhpcyk7XG4gICAgfVxuICB9O1xuXG4gIF9wcm90by5kdXJhdGlvbiA9IGZ1bmN0aW9uIGR1cmF0aW9uKCkge1xuICAgIHJldHVybiBnZXREdXJhdGlvbih0aGlzLl9zdGFydCwgdGhpcy5fZW5kKTtcbiAgfTtcblxuICByZXR1cm4gU3BhbkJhc2U7XG59KCk7XG5cbmV4cG9ydCBkZWZhdWx0IFNwYW5CYXNlOyIsImZ1bmN0aW9uIF9pbmhlcml0c0xvb3NlKHN1YkNsYXNzLCBzdXBlckNsYXNzKSB7IHN1YkNsYXNzLnByb3RvdHlwZSA9IE9iamVjdC5jcmVhdGUoc3VwZXJDbGFzcy5wcm90b3R5cGUpOyBzdWJDbGFzcy5wcm90b3R5cGUuY29uc3RydWN0b3IgPSBzdWJDbGFzczsgX3NldFByb3RvdHlwZU9mKHN1YkNsYXNzLCBzdXBlckNsYXNzKTsgfVxuXG5mdW5jdGlvbiBfc2V0UHJvdG90eXBlT2YobywgcCkgeyBfc2V0UHJvdG90eXBlT2YgPSBPYmplY3Quc2V0UHJvdG90eXBlT2YgfHwgZnVuY3Rpb24gX3NldFByb3RvdHlwZU9mKG8sIHApIHsgby5fX3Byb3RvX18gPSBwOyByZXR1cm4gbzsgfTsgcmV0dXJuIF9zZXRQcm90b3R5cGVPZihvLCBwKTsgfVxuXG5pbXBvcnQgU3BhbkJhc2UgZnJvbSAnLi9zcGFuLWJhc2UnO1xuaW1wb3J0IHsgYWRkU3BhbkNvbnRleHQgfSBmcm9tICcuLi9jb21tb24vY29udGV4dCc7XG5cbnZhciBTcGFuID0gZnVuY3Rpb24gKF9TcGFuQmFzZSkge1xuICBfaW5oZXJpdHNMb29zZShTcGFuLCBfU3BhbkJhc2UpO1xuXG4gIGZ1bmN0aW9uIFNwYW4obmFtZSwgdHlwZSwgb3B0aW9ucykge1xuICAgIHZhciBfdGhpcztcblxuICAgIF90aGlzID0gX1NwYW5CYXNlLmNhbGwodGhpcywgbmFtZSwgdHlwZSwgb3B0aW9ucykgfHwgdGhpcztcbiAgICBfdGhpcy5wYXJlbnRJZCA9IF90aGlzLm9wdGlvbnMucGFyZW50SWQ7XG4gICAgX3RoaXMuc3VidHlwZSA9IHVuZGVmaW5lZDtcbiAgICBfdGhpcy5hY3Rpb24gPSB1bmRlZmluZWQ7XG5cbiAgICBpZiAoX3RoaXMudHlwZS5pbmRleE9mKCcuJykgIT09IC0xKSB7XG4gICAgICB2YXIgZmllbGRzID0gX3RoaXMudHlwZS5zcGxpdCgnLicsIDMpO1xuXG4gICAgICBfdGhpcy50eXBlID0gZmllbGRzWzBdO1xuICAgICAgX3RoaXMuc3VidHlwZSA9IGZpZWxkc1sxXTtcbiAgICAgIF90aGlzLmFjdGlvbiA9IGZpZWxkc1syXTtcbiAgICB9XG5cbiAgICBfdGhpcy5zeW5jID0gX3RoaXMub3B0aW9ucy5zeW5jO1xuICAgIHJldHVybiBfdGhpcztcbiAgfVxuXG4gIHZhciBfcHJvdG8gPSBTcGFuLnByb3RvdHlwZTtcblxuICBfcHJvdG8uZW5kID0gZnVuY3Rpb24gZW5kKGVuZFRpbWUsIGRhdGEpIHtcbiAgICBfU3BhbkJhc2UucHJvdG90eXBlLmVuZC5jYWxsKHRoaXMsIGVuZFRpbWUpO1xuXG4gICAgYWRkU3BhbkNvbnRleHQodGhpcywgZGF0YSk7XG4gIH07XG5cbiAgcmV0dXJuIFNwYW47XG59KFNwYW5CYXNlKTtcblxuZXhwb3J0IGRlZmF1bHQgU3BhbjsiLCJpbXBvcnQgeyBQcm9taXNlIH0gZnJvbSAnLi4vY29tbW9uL3BvbHlmaWxscyc7XG5pbXBvcnQgVHJhbnNhY3Rpb24gZnJvbSAnLi90cmFuc2FjdGlvbic7XG5pbXBvcnQgeyBQZXJmRW50cnlSZWNvcmRlciwgY2FwdHVyZU9ic2VydmVyRW50cmllcywgbWV0cmljcywgY3JlYXRlVG90YWxCbG9ja2luZ1RpbWVTcGFuIH0gZnJvbSAnLi9tZXRyaWNzJztcbmltcG9ydCB7IGV4dGVuZCwgZ2V0RWFybGllc3RTcGFuLCBnZXRMYXRlc3ROb25YSFJTcGFuLCBnZXRMYXRlc3RYSFJTcGFuLCBpc1BlcmZUeXBlU3VwcG9ydGVkLCBnZW5lcmF0ZVJhbmRvbUlkIH0gZnJvbSAnLi4vY29tbW9uL3V0aWxzJztcbmltcG9ydCB7IGNhcHR1cmVOYXZpZ2F0aW9uIH0gZnJvbSAnLi9jYXB0dXJlLW5hdmlnYXRpb24nO1xuaW1wb3J0IHsgUEFHRV9MT0FELCBOQU1FX1VOS05PV04sIFRSQU5TQUNUSU9OX1NUQVJULCBUUkFOU0FDVElPTl9FTkQsIFRFTVBPUkFSWV9UWVBFLCBUUkFOU0FDVElPTl9UWVBFX09SREVSLCBMQVJHRVNUX0NPTlRFTlRGVUxfUEFJTlQsIExPTkdfVEFTSywgUEFJTlQsIFRSVU5DQVRFRF9UWVBFLCBGSVJTVF9JTlBVVCwgTEFZT1VUX1NISUZULCBTRVNTSU9OX1RJTUVPVVQsIFBBR0VfTE9BRF9ERUxBWSB9IGZyb20gJy4uL2NvbW1vbi9jb25zdGFudHMnO1xuaW1wb3J0IHsgYWRkVHJhbnNhY3Rpb25Db250ZXh0IH0gZnJvbSAnLi4vY29tbW9uL2NvbnRleHQnO1xuaW1wb3J0IHsgX19ERVZfXywgc3RhdGUgfSBmcm9tICcuLi9zdGF0ZSc7XG5pbXBvcnQgeyBzbHVnaWZ5VXJsIH0gZnJvbSAnLi4vY29tbW9uL3VybCc7XG5cbnZhciBUcmFuc2FjdGlvblNlcnZpY2UgPSBmdW5jdGlvbiAoKSB7XG4gIGZ1bmN0aW9uIFRyYW5zYWN0aW9uU2VydmljZShsb2dnZXIsIGNvbmZpZykge1xuICAgIHZhciBfdGhpcyA9IHRoaXM7XG5cbiAgICB0aGlzLl9jb25maWcgPSBjb25maWc7XG4gICAgdGhpcy5fbG9nZ2VyID0gbG9nZ2VyO1xuICAgIHRoaXMuY3VycmVudFRyYW5zYWN0aW9uID0gdW5kZWZpbmVkO1xuICAgIHRoaXMucmVzcEludGVydmFsSWQgPSB1bmRlZmluZWQ7XG4gICAgdGhpcy5yZWNvcmRlciA9IG5ldyBQZXJmRW50cnlSZWNvcmRlcihmdW5jdGlvbiAobGlzdCkge1xuICAgICAgdmFyIHRyID0gX3RoaXMuZ2V0Q3VycmVudFRyYW5zYWN0aW9uKCk7XG5cbiAgICAgIGlmICh0ciAmJiB0ci5jYXB0dXJlVGltaW5ncykge1xuICAgICAgICB2YXIgX3RyJHNwYW5zO1xuXG4gICAgICAgIHZhciBpc0hhcmROYXZpZ2F0aW9uID0gdHIudHlwZSA9PT0gUEFHRV9MT0FEO1xuXG4gICAgICAgIHZhciBfY2FwdHVyZU9ic2VydmVyRW50cmkgPSBjYXB0dXJlT2JzZXJ2ZXJFbnRyaWVzKGxpc3QsIHtcbiAgICAgICAgICBpc0hhcmROYXZpZ2F0aW9uOiBpc0hhcmROYXZpZ2F0aW9uLFxuICAgICAgICAgIHRyU3RhcnQ6IGlzSGFyZE5hdmlnYXRpb24gPyAwIDogdHIuX3N0YXJ0XG4gICAgICAgIH0pLFxuICAgICAgICAgICAgc3BhbnMgPSBfY2FwdHVyZU9ic2VydmVyRW50cmkuc3BhbnMsXG4gICAgICAgICAgICBtYXJrcyA9IF9jYXB0dXJlT2JzZXJ2ZXJFbnRyaS5tYXJrcztcblxuICAgICAgICAoX3RyJHNwYW5zID0gdHIuc3BhbnMpLnB1c2guYXBwbHkoX3RyJHNwYW5zLCBzcGFucyk7XG5cbiAgICAgICAgdHIuYWRkTWFya3Moe1xuICAgICAgICAgIGFnZW50OiBtYXJrc1xuICAgICAgICB9KTtcbiAgICAgIH1cbiAgICB9KTtcbiAgfVxuXG4gIHZhciBfcHJvdG8gPSBUcmFuc2FjdGlvblNlcnZpY2UucHJvdG90eXBlO1xuXG4gIF9wcm90by5jcmVhdGVDdXJyZW50VHJhbnNhY3Rpb24gPSBmdW5jdGlvbiBjcmVhdGVDdXJyZW50VHJhbnNhY3Rpb24obmFtZSwgdHlwZSwgb3B0aW9ucykge1xuICAgIHZhciB0ciA9IG5ldyBUcmFuc2FjdGlvbihuYW1lLCB0eXBlLCBvcHRpb25zKTtcbiAgICB0aGlzLmN1cnJlbnRUcmFuc2FjdGlvbiA9IHRyO1xuICAgIHJldHVybiB0cjtcbiAgfTtcblxuICBfcHJvdG8uZ2V0Q3VycmVudFRyYW5zYWN0aW9uID0gZnVuY3Rpb24gZ2V0Q3VycmVudFRyYW5zYWN0aW9uKCkge1xuICAgIGlmICh0aGlzLmN1cnJlbnRUcmFuc2FjdGlvbiAmJiAhdGhpcy5jdXJyZW50VHJhbnNhY3Rpb24uZW5kZWQpIHtcbiAgICAgIHJldHVybiB0aGlzLmN1cnJlbnRUcmFuc2FjdGlvbjtcbiAgICB9XG4gIH07XG5cbiAgX3Byb3RvLmNyZWF0ZU9wdGlvbnMgPSBmdW5jdGlvbiBjcmVhdGVPcHRpb25zKG9wdGlvbnMpIHtcbiAgICB2YXIgY29uZmlnID0gdGhpcy5fY29uZmlnLmNvbmZpZztcbiAgICB2YXIgcHJlc2V0T3B0aW9ucyA9IHtcbiAgICAgIHRyYW5zYWN0aW9uU2FtcGxlUmF0ZTogY29uZmlnLnRyYW5zYWN0aW9uU2FtcGxlUmF0ZVxuICAgIH07XG4gICAgdmFyIHBlcmZPcHRpb25zID0gZXh0ZW5kKHByZXNldE9wdGlvbnMsIG9wdGlvbnMpO1xuXG4gICAgaWYgKHBlcmZPcHRpb25zLm1hbmFnZWQpIHtcbiAgICAgIHBlcmZPcHRpb25zID0gZXh0ZW5kKHtcbiAgICAgICAgcGFnZUxvYWRUcmFjZUlkOiBjb25maWcucGFnZUxvYWRUcmFjZUlkLFxuICAgICAgICBwYWdlTG9hZFNhbXBsZWQ6IGNvbmZpZy5wYWdlTG9hZFNhbXBsZWQsXG4gICAgICAgIHBhZ2VMb2FkU3BhbklkOiBjb25maWcucGFnZUxvYWRTcGFuSWQsXG4gICAgICAgIHBhZ2VMb2FkVHJhbnNhY3Rpb25OYW1lOiBjb25maWcucGFnZUxvYWRUcmFuc2FjdGlvbk5hbWVcbiAgICAgIH0sIHBlcmZPcHRpb25zKTtcbiAgICB9XG5cbiAgICByZXR1cm4gcGVyZk9wdGlvbnM7XG4gIH07XG5cbiAgX3Byb3RvLnN0YXJ0TWFuYWdlZFRyYW5zYWN0aW9uID0gZnVuY3Rpb24gc3RhcnRNYW5hZ2VkVHJhbnNhY3Rpb24obmFtZSwgdHlwZSwgcGVyZk9wdGlvbnMpIHtcbiAgICB2YXIgdHIgPSB0aGlzLmdldEN1cnJlbnRUcmFuc2FjdGlvbigpO1xuICAgIHZhciBpc1JlZGVmaW5lZCA9IGZhbHNlO1xuXG4gICAgaWYgKCF0cikge1xuICAgICAgdHIgPSB0aGlzLmNyZWF0ZUN1cnJlbnRUcmFuc2FjdGlvbihuYW1lLCB0eXBlLCBwZXJmT3B0aW9ucyk7XG4gICAgfSBlbHNlIGlmICh0ci5jYW5SZXVzZSgpICYmIHBlcmZPcHRpb25zLmNhblJldXNlKSB7XG4gICAgICB2YXIgcmVkZWZpbmVUeXBlID0gdHIudHlwZTtcbiAgICAgIHZhciBjdXJyZW50VHlwZU9yZGVyID0gVFJBTlNBQ1RJT05fVFlQRV9PUkRFUi5pbmRleE9mKHRyLnR5cGUpO1xuICAgICAgdmFyIHJlZGVmaW5lVHlwZU9yZGVyID0gVFJBTlNBQ1RJT05fVFlQRV9PUkRFUi5pbmRleE9mKHR5cGUpO1xuXG4gICAgICBpZiAoY3VycmVudFR5cGVPcmRlciA+PSAwICYmIHJlZGVmaW5lVHlwZU9yZGVyIDwgY3VycmVudFR5cGVPcmRlcikge1xuICAgICAgICByZWRlZmluZVR5cGUgPSB0eXBlO1xuICAgICAgfVxuXG4gICAgICBpZiAoX19ERVZfXykge1xuICAgICAgICB0aGlzLl9sb2dnZXIuZGVidWcoXCJyZWRlZmluaW5nIHRyYW5zYWN0aW9uKFwiICsgdHIuaWQgKyBcIiwgXCIgKyB0ci5uYW1lICsgXCIsIFwiICsgdHIudHlwZSArIFwiKVwiLCAndG8nLCBcIihcIiArIChuYW1lIHx8IHRyLm5hbWUpICsgXCIsIFwiICsgcmVkZWZpbmVUeXBlICsgXCIpXCIsIHRyKTtcbiAgICAgIH1cblxuICAgICAgdHIucmVkZWZpbmUobmFtZSwgcmVkZWZpbmVUeXBlLCBwZXJmT3B0aW9ucyk7XG4gICAgICBpc1JlZGVmaW5lZCA9IHRydWU7XG4gICAgfSBlbHNlIHtcbiAgICAgIGlmIChfX0RFVl9fKSB7XG4gICAgICAgIHRoaXMuX2xvZ2dlci5kZWJ1ZyhcImVuZGluZyBwcmV2aW91cyB0cmFuc2FjdGlvbihcIiArIHRyLmlkICsgXCIsIFwiICsgdHIubmFtZSArIFwiKVwiLCB0cik7XG4gICAgICB9XG5cbiAgICAgIHRyLmVuZCgpO1xuICAgICAgdHIgPSB0aGlzLmNyZWF0ZUN1cnJlbnRUcmFuc2FjdGlvbihuYW1lLCB0eXBlLCBwZXJmT3B0aW9ucyk7XG4gICAgfVxuXG4gICAgaWYgKHRyLnR5cGUgPT09IFBBR0VfTE9BRCkge1xuICAgICAgaWYgKCFpc1JlZGVmaW5lZCkge1xuICAgICAgICB0aGlzLnJlY29yZGVyLnN0YXJ0KExBUkdFU1RfQ09OVEVOVEZVTF9QQUlOVCk7XG4gICAgICAgIHRoaXMucmVjb3JkZXIuc3RhcnQoUEFJTlQpO1xuICAgICAgICB0aGlzLnJlY29yZGVyLnN0YXJ0KEZJUlNUX0lOUFVUKTtcbiAgICAgICAgdGhpcy5yZWNvcmRlci5zdGFydChMQVlPVVRfU0hJRlQpO1xuICAgICAgfVxuXG4gICAgICBpZiAocGVyZk9wdGlvbnMucGFnZUxvYWRUcmFjZUlkKSB7XG4gICAgICAgIHRyLnRyYWNlSWQgPSBwZXJmT3B0aW9ucy5wYWdlTG9hZFRyYWNlSWQ7XG4gICAgICB9XG5cbiAgICAgIGlmIChwZXJmT3B0aW9ucy5wYWdlTG9hZFNhbXBsZWQpIHtcbiAgICAgICAgdHIuc2FtcGxlZCA9IHBlcmZPcHRpb25zLnBhZ2VMb2FkU2FtcGxlZDtcbiAgICAgIH1cblxuICAgICAgaWYgKHRyLm5hbWUgPT09IE5BTUVfVU5LTk9XTiAmJiBwZXJmT3B0aW9ucy5wYWdlTG9hZFRyYW5zYWN0aW9uTmFtZSkge1xuICAgICAgICB0ci5uYW1lID0gcGVyZk9wdGlvbnMucGFnZUxvYWRUcmFuc2FjdGlvbk5hbWU7XG4gICAgICB9XG4gICAgfVxuXG4gICAgaWYgKCFpc1JlZGVmaW5lZCAmJiB0aGlzLl9jb25maWcuZ2V0KCdtb25pdG9yTG9uZ3Rhc2tzJykpIHtcbiAgICAgIHRoaXMucmVjb3JkZXIuc3RhcnQoTE9OR19UQVNLKTtcbiAgICB9XG5cbiAgICBpZiAodHIuc2FtcGxlZCkge1xuICAgICAgdHIuY2FwdHVyZVRpbWluZ3MgPSB0cnVlO1xuICAgIH1cblxuICAgIHJldHVybiB0cjtcbiAgfTtcblxuICBfcHJvdG8uc3RhcnRUcmFuc2FjdGlvbiA9IGZ1bmN0aW9uIHN0YXJ0VHJhbnNhY3Rpb24obmFtZSwgdHlwZSwgb3B0aW9ucykge1xuICAgIHZhciBfdGhpczIgPSB0aGlzO1xuXG4gICAgdmFyIHBlcmZPcHRpb25zID0gdGhpcy5jcmVhdGVPcHRpb25zKG9wdGlvbnMpO1xuICAgIHZhciB0cjtcbiAgICB2YXIgZmlyZU9uc3RhcnRIb29rID0gdHJ1ZTtcblxuICAgIGlmIChwZXJmT3B0aW9ucy5tYW5hZ2VkKSB7XG4gICAgICB2YXIgY3VycmVudCA9IHRoaXMuY3VycmVudFRyYW5zYWN0aW9uO1xuICAgICAgdHIgPSB0aGlzLnN0YXJ0TWFuYWdlZFRyYW5zYWN0aW9uKG5hbWUsIHR5cGUsIHBlcmZPcHRpb25zKTtcblxuICAgICAgaWYgKGN1cnJlbnQgPT09IHRyKSB7XG4gICAgICAgIGZpcmVPbnN0YXJ0SG9vayA9IGZhbHNlO1xuICAgICAgfVxuICAgIH0gZWxzZSB7XG4gICAgICB0ciA9IG5ldyBUcmFuc2FjdGlvbihuYW1lLCB0eXBlLCBwZXJmT3B0aW9ucyk7XG4gICAgfVxuXG4gICAgdHIub25FbmQgPSBmdW5jdGlvbiAoKSB7XG4gICAgICByZXR1cm4gX3RoaXMyLmhhbmRsZVRyYW5zYWN0aW9uRW5kKHRyKTtcbiAgICB9O1xuXG4gICAgaWYgKGZpcmVPbnN0YXJ0SG9vaykge1xuICAgICAgaWYgKF9fREVWX18pIHtcbiAgICAgICAgdGhpcy5fbG9nZ2VyLmRlYnVnKFwic3RhcnRUcmFuc2FjdGlvbihcIiArIHRyLmlkICsgXCIsIFwiICsgdHIubmFtZSArIFwiLCBcIiArIHRyLnR5cGUgKyBcIilcIik7XG4gICAgICB9XG5cbiAgICAgIHRoaXMuX2NvbmZpZy5ldmVudHMuc2VuZChUUkFOU0FDVElPTl9TVEFSVCwgW3RyXSk7XG4gICAgfVxuXG4gICAgcmV0dXJuIHRyO1xuICB9O1xuXG4gIF9wcm90by5oYW5kbGVUcmFuc2FjdGlvbkVuZCA9IGZ1bmN0aW9uIGhhbmRsZVRyYW5zYWN0aW9uRW5kKHRyKSB7XG4gICAgdmFyIF90aGlzMyA9IHRoaXM7XG5cbiAgICB0aGlzLnJlY29yZGVyLnN0b3AoKTtcbiAgICB2YXIgY3VycmVudFVybCA9IHdpbmRvdy5sb2NhdGlvbi5ocmVmO1xuICAgIHJldHVybiBQcm9taXNlLnJlc29sdmUoKS50aGVuKGZ1bmN0aW9uICgpIHtcbiAgICAgIHZhciBuYW1lID0gdHIubmFtZSxcbiAgICAgICAgICB0eXBlID0gdHIudHlwZTtcbiAgICAgIHZhciBsYXN0SGlkZGVuU3RhcnQgPSBzdGF0ZS5sYXN0SGlkZGVuU3RhcnQ7XG5cbiAgICAgIGlmIChsYXN0SGlkZGVuU3RhcnQgPj0gdHIuX3N0YXJ0KSB7XG4gICAgICAgIGlmIChfX0RFVl9fKSB7XG4gICAgICAgICAgX3RoaXMzLl9sb2dnZXIuZGVidWcoXCJ0cmFuc2FjdGlvbihcIiArIHRyLmlkICsgXCIsIFwiICsgbmFtZSArIFwiLCBcIiArIHR5cGUgKyBcIikgd2FzIGRpc2NhcmRlZCEgVGhlIHBhZ2Ugd2FzIGhpZGRlbiBkdXJpbmcgdGhlIHRyYW5zYWN0aW9uIVwiKTtcbiAgICAgICAgfVxuXG4gICAgICAgIHJldHVybjtcbiAgICAgIH1cblxuICAgICAgaWYgKF90aGlzMy5zaG91bGRJZ25vcmVUcmFuc2FjdGlvbihuYW1lKSB8fCB0eXBlID09PSBURU1QT1JBUllfVFlQRSkge1xuICAgICAgICBpZiAoX19ERVZfXykge1xuICAgICAgICAgIF90aGlzMy5fbG9nZ2VyLmRlYnVnKFwidHJhbnNhY3Rpb24oXCIgKyB0ci5pZCArIFwiLCBcIiArIG5hbWUgKyBcIiwgXCIgKyB0eXBlICsgXCIpIGlzIGlnbm9yZWRcIik7XG4gICAgICAgIH1cblxuICAgICAgICByZXR1cm47XG4gICAgICB9XG5cbiAgICAgIGlmICh0eXBlID09PSBQQUdFX0xPQUQpIHtcbiAgICAgICAgdmFyIHBhZ2VMb2FkVHJhbnNhY3Rpb25OYW1lID0gX3RoaXMzLl9jb25maWcuZ2V0KCdwYWdlTG9hZFRyYW5zYWN0aW9uTmFtZScpO1xuXG4gICAgICAgIGlmIChuYW1lID09PSBOQU1FX1VOS05PV04gJiYgcGFnZUxvYWRUcmFuc2FjdGlvbk5hbWUpIHtcbiAgICAgICAgICB0ci5uYW1lID0gcGFnZUxvYWRUcmFuc2FjdGlvbk5hbWU7XG4gICAgICAgIH1cblxuICAgICAgICBpZiAodHIuY2FwdHVyZVRpbWluZ3MpIHtcbiAgICAgICAgICB2YXIgY2xzID0gbWV0cmljcy5jbHMsXG4gICAgICAgICAgICAgIGZpZCA9IG1ldHJpY3MuZmlkLFxuICAgICAgICAgICAgICB0YnQgPSBtZXRyaWNzLnRidCxcbiAgICAgICAgICAgICAgbG9uZ3Rhc2sgPSBtZXRyaWNzLmxvbmd0YXNrO1xuXG4gICAgICAgICAgaWYgKHRidC5kdXJhdGlvbiA+IDApIHtcbiAgICAgICAgICAgIHRyLnNwYW5zLnB1c2goY3JlYXRlVG90YWxCbG9ja2luZ1RpbWVTcGFuKHRidCkpO1xuICAgICAgICAgIH1cblxuICAgICAgICAgIHRyLmV4cGVyaWVuY2UgPSB7fTtcblxuICAgICAgICAgIGlmIChpc1BlcmZUeXBlU3VwcG9ydGVkKExPTkdfVEFTSykpIHtcbiAgICAgICAgICAgIHRyLmV4cGVyaWVuY2UudGJ0ID0gdGJ0LmR1cmF0aW9uO1xuICAgICAgICAgIH1cblxuICAgICAgICAgIGlmIChpc1BlcmZUeXBlU3VwcG9ydGVkKExBWU9VVF9TSElGVCkpIHtcbiAgICAgICAgICAgIHRyLmV4cGVyaWVuY2UuY2xzID0gY2xzLnNjb3JlO1xuICAgICAgICAgIH1cblxuICAgICAgICAgIGlmIChmaWQgPiAwKSB7XG4gICAgICAgICAgICB0ci5leHBlcmllbmNlLmZpZCA9IGZpZDtcbiAgICAgICAgICB9XG5cbiAgICAgICAgICBpZiAobG9uZ3Rhc2suY291bnQgPiAwKSB7XG4gICAgICAgICAgICB0ci5leHBlcmllbmNlLmxvbmd0YXNrID0ge1xuICAgICAgICAgICAgICBjb3VudDogbG9uZ3Rhc2suY291bnQsXG4gICAgICAgICAgICAgIHN1bTogbG9uZ3Rhc2suZHVyYXRpb24sXG4gICAgICAgICAgICAgIG1heDogbG9uZ3Rhc2subWF4XG4gICAgICAgICAgICB9O1xuICAgICAgICAgIH1cbiAgICAgICAgfVxuXG4gICAgICAgIF90aGlzMy5zZXRTZXNzaW9uKHRyKTtcbiAgICAgIH1cblxuICAgICAgaWYgKHRyLm5hbWUgPT09IE5BTUVfVU5LTk9XTikge1xuICAgICAgICB0ci5uYW1lID0gc2x1Z2lmeVVybChjdXJyZW50VXJsKTtcbiAgICAgIH1cblxuICAgICAgY2FwdHVyZU5hdmlnYXRpb24odHIpO1xuXG4gICAgICBfdGhpczMuYWRqdXN0VHJhbnNhY3Rpb25UaW1lKHRyKTtcblxuICAgICAgdmFyIGJyZWFrZG93bk1ldHJpY3MgPSBfdGhpczMuX2NvbmZpZy5nZXQoJ2JyZWFrZG93bk1ldHJpY3MnKTtcblxuICAgICAgaWYgKGJyZWFrZG93bk1ldHJpY3MpIHtcbiAgICAgICAgdHIuY2FwdHVyZUJyZWFrZG93bigpO1xuICAgICAgfVxuXG4gICAgICB2YXIgY29uZmlnQ29udGV4dCA9IF90aGlzMy5fY29uZmlnLmdldCgnY29udGV4dCcpO1xuXG4gICAgICBhZGRUcmFuc2FjdGlvbkNvbnRleHQodHIsIGNvbmZpZ0NvbnRleHQpO1xuXG4gICAgICBfdGhpczMuX2NvbmZpZy5ldmVudHMuc2VuZChUUkFOU0FDVElPTl9FTkQsIFt0cl0pO1xuXG4gICAgICBpZiAoX19ERVZfXykge1xuICAgICAgICBfdGhpczMuX2xvZ2dlci5kZWJ1ZyhcImVuZCB0cmFuc2FjdGlvbihcIiArIHRyLmlkICsgXCIsIFwiICsgdHIubmFtZSArIFwiLCBcIiArIHRyLnR5cGUgKyBcIilcIiwgdHIpO1xuICAgICAgfVxuICAgIH0sIGZ1bmN0aW9uIChlcnIpIHtcbiAgICAgIGlmIChfX0RFVl9fKSB7XG4gICAgICAgIF90aGlzMy5fbG9nZ2VyLmRlYnVnKFwiZXJyb3IgZW5kaW5nIHRyYW5zYWN0aW9uKFwiICsgdHIuaWQgKyBcIiwgXCIgKyB0ci5uYW1lICsgXCIpXCIsIGVycik7XG4gICAgICB9XG4gICAgfSk7XG4gIH07XG5cbiAgX3Byb3RvLnNldFNlc3Npb24gPSBmdW5jdGlvbiBzZXRTZXNzaW9uKHRyKSB7XG4gICAgdmFyIHNlc3Npb24gPSB0aGlzLl9jb25maWcuZ2V0KCdzZXNzaW9uJyk7XG5cbiAgICBpZiAoc2Vzc2lvbikge1xuICAgICAgaWYgKHR5cGVvZiBzZXNzaW9uID09ICdib29sZWFuJykge1xuICAgICAgICB0ci5zZXNzaW9uID0ge1xuICAgICAgICAgIGlkOiBnZW5lcmF0ZVJhbmRvbUlkKDE2KSxcbiAgICAgICAgICBzZXF1ZW5jZTogMVxuICAgICAgICB9O1xuICAgICAgfSBlbHNlIHtcbiAgICAgICAgaWYgKHNlc3Npb24udGltZXN0YW1wICYmIERhdGUubm93KCkgLSBzZXNzaW9uLnRpbWVzdGFtcCA+IFNFU1NJT05fVElNRU9VVCkge1xuICAgICAgICAgIHRyLnNlc3Npb24gPSB7XG4gICAgICAgICAgICBpZDogZ2VuZXJhdGVSYW5kb21JZCgxNiksXG4gICAgICAgICAgICBzZXF1ZW5jZTogMVxuICAgICAgICAgIH07XG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgdHIuc2Vzc2lvbiA9IHtcbiAgICAgICAgICAgIGlkOiBzZXNzaW9uLmlkLFxuICAgICAgICAgICAgc2VxdWVuY2U6IHNlc3Npb24uc2VxdWVuY2UgPyBzZXNzaW9uLnNlcXVlbmNlICsgMSA6IDFcbiAgICAgICAgICB9O1xuICAgICAgICB9XG4gICAgICB9XG5cbiAgICAgIHZhciBzZXNzaW9uQ29uZmlnID0ge1xuICAgICAgICBzZXNzaW9uOiB7XG4gICAgICAgICAgaWQ6IHRyLnNlc3Npb24uaWQsXG4gICAgICAgICAgc2VxdWVuY2U6IHRyLnNlc3Npb24uc2VxdWVuY2UsXG4gICAgICAgICAgdGltZXN0YW1wOiBEYXRlLm5vdygpXG4gICAgICAgIH1cbiAgICAgIH07XG5cbiAgICAgIHRoaXMuX2NvbmZpZy5zZXRDb25maWcoc2Vzc2lvbkNvbmZpZyk7XG5cbiAgICAgIHRoaXMuX2NvbmZpZy5zZXRMb2NhbENvbmZpZyhzZXNzaW9uQ29uZmlnLCB0cnVlKTtcbiAgICB9XG4gIH07XG5cbiAgX3Byb3RvLmFkanVzdFRyYW5zYWN0aW9uVGltZSA9IGZ1bmN0aW9uIGFkanVzdFRyYW5zYWN0aW9uVGltZSh0cmFuc2FjdGlvbikge1xuICAgIHZhciBzcGFucyA9IHRyYW5zYWN0aW9uLnNwYW5zO1xuICAgIHZhciBlYXJsaWVzdFNwYW4gPSBnZXRFYXJsaWVzdFNwYW4oc3BhbnMpO1xuXG4gICAgaWYgKGVhcmxpZXN0U3BhbiAmJiBlYXJsaWVzdFNwYW4uX3N0YXJ0IDwgdHJhbnNhY3Rpb24uX3N0YXJ0KSB7XG4gICAgICB0cmFuc2FjdGlvbi5fc3RhcnQgPSBlYXJsaWVzdFNwYW4uX3N0YXJ0O1xuICAgIH1cblxuICAgIHZhciBsYXRlc3RTcGFuID0gZ2V0TGF0ZXN0Tm9uWEhSU3BhbihzcGFucykgfHwge307XG4gICAgdmFyIGxhdGVzdFNwYW5FbmQgPSBsYXRlc3RTcGFuLl9lbmQgfHwgMDtcblxuICAgIGlmICh0cmFuc2FjdGlvbi50eXBlID09PSBQQUdFX0xPQUQpIHtcbiAgICAgIHZhciB0cmFuc2FjdGlvbkVuZFdpdGhvdXREZWxheSA9IHRyYW5zYWN0aW9uLl9lbmQgLSBQQUdFX0xPQURfREVMQVk7XG4gICAgICB2YXIgbGNwID0gbWV0cmljcy5sY3AgfHwgMDtcbiAgICAgIHZhciBsYXRlc3RYSFJTcGFuID0gZ2V0TGF0ZXN0WEhSU3BhbihzcGFucykgfHwge307XG4gICAgICB2YXIgbGF0ZXN0WEhSU3BhbkVuZCA9IGxhdGVzdFhIUlNwYW4uX2VuZCB8fCAwO1xuICAgICAgdHJhbnNhY3Rpb24uX2VuZCA9IE1hdGgubWF4KGxhdGVzdFNwYW5FbmQsIGxhdGVzdFhIUlNwYW5FbmQsIGxjcCwgdHJhbnNhY3Rpb25FbmRXaXRob3V0RGVsYXkpO1xuICAgIH0gZWxzZSBpZiAobGF0ZXN0U3BhbkVuZCA+IHRyYW5zYWN0aW9uLl9lbmQpIHtcbiAgICAgIHRyYW5zYWN0aW9uLl9lbmQgPSBsYXRlc3RTcGFuRW5kO1xuICAgIH1cblxuICAgIHRoaXMudHJ1bmNhdGVTcGFucyhzcGFucywgdHJhbnNhY3Rpb24uX2VuZCk7XG4gIH07XG5cbiAgX3Byb3RvLnRydW5jYXRlU3BhbnMgPSBmdW5jdGlvbiB0cnVuY2F0ZVNwYW5zKHNwYW5zLCB0cmFuc2FjdGlvbkVuZCkge1xuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgc3BhbnMubGVuZ3RoOyBpKyspIHtcbiAgICAgIHZhciBzcGFuID0gc3BhbnNbaV07XG5cbiAgICAgIGlmIChzcGFuLl9lbmQgPiB0cmFuc2FjdGlvbkVuZCkge1xuICAgICAgICBzcGFuLl9lbmQgPSB0cmFuc2FjdGlvbkVuZDtcbiAgICAgICAgc3Bhbi50eXBlICs9IFRSVU5DQVRFRF9UWVBFO1xuICAgICAgfVxuXG4gICAgICBpZiAoc3Bhbi5fc3RhcnQgPiB0cmFuc2FjdGlvbkVuZCkge1xuICAgICAgICBzcGFuLl9zdGFydCA9IHRyYW5zYWN0aW9uRW5kO1xuICAgICAgfVxuICAgIH1cbiAgfTtcblxuICBfcHJvdG8uc2hvdWxkSWdub3JlVHJhbnNhY3Rpb24gPSBmdW5jdGlvbiBzaG91bGRJZ25vcmVUcmFuc2FjdGlvbih0cmFuc2FjdGlvbk5hbWUpIHtcbiAgICB2YXIgaWdub3JlTGlzdCA9IHRoaXMuX2NvbmZpZy5nZXQoJ2lnbm9yZVRyYW5zYWN0aW9ucycpO1xuXG4gICAgaWYgKGlnbm9yZUxpc3QgJiYgaWdub3JlTGlzdC5sZW5ndGgpIHtcbiAgICAgIGZvciAodmFyIGkgPSAwOyBpIDwgaWdub3JlTGlzdC5sZW5ndGg7IGkrKykge1xuICAgICAgICB2YXIgZWxlbWVudCA9IGlnbm9yZUxpc3RbaV07XG5cbiAgICAgICAgaWYgKHR5cGVvZiBlbGVtZW50LnRlc3QgPT09ICdmdW5jdGlvbicpIHtcbiAgICAgICAgICBpZiAoZWxlbWVudC50ZXN0KHRyYW5zYWN0aW9uTmFtZSkpIHtcbiAgICAgICAgICAgIHJldHVybiB0cnVlO1xuICAgICAgICAgIH1cbiAgICAgICAgfSBlbHNlIGlmIChlbGVtZW50ID09PSB0cmFuc2FjdGlvbk5hbWUpIHtcbiAgICAgICAgICByZXR1cm4gdHJ1ZTtcbiAgICAgICAgfVxuICAgICAgfVxuICAgIH1cblxuICAgIHJldHVybiBmYWxzZTtcbiAgfTtcblxuICBfcHJvdG8uc3RhcnRTcGFuID0gZnVuY3Rpb24gc3RhcnRTcGFuKG5hbWUsIHR5cGUsIG9wdGlvbnMpIHtcbiAgICB2YXIgdHIgPSB0aGlzLmdldEN1cnJlbnRUcmFuc2FjdGlvbigpO1xuXG4gICAgaWYgKCF0cikge1xuICAgICAgdHIgPSB0aGlzLmNyZWF0ZUN1cnJlbnRUcmFuc2FjdGlvbih1bmRlZmluZWQsIFRFTVBPUkFSWV9UWVBFLCB0aGlzLmNyZWF0ZU9wdGlvbnMoe1xuICAgICAgICBjYW5SZXVzZTogdHJ1ZSxcbiAgICAgICAgbWFuYWdlZDogdHJ1ZVxuICAgICAgfSkpO1xuICAgIH1cblxuICAgIHZhciBzcGFuID0gdHIuc3RhcnRTcGFuKG5hbWUsIHR5cGUsIG9wdGlvbnMpO1xuXG4gICAgaWYgKF9fREVWX18pIHtcbiAgICAgIHRoaXMuX2xvZ2dlci5kZWJ1ZyhcInN0YXJ0U3BhbihcIiArIG5hbWUgKyBcIiwgXCIgKyBzcGFuLnR5cGUgKyBcIilcIiwgXCJvbiB0cmFuc2FjdGlvbihcIiArIHRyLmlkICsgXCIsIFwiICsgdHIubmFtZSArIFwiKVwiKTtcbiAgICB9XG5cbiAgICByZXR1cm4gc3BhbjtcbiAgfTtcblxuICBfcHJvdG8uZW5kU3BhbiA9IGZ1bmN0aW9uIGVuZFNwYW4oc3BhbiwgY29udGV4dCkge1xuICAgIGlmICghc3Bhbikge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIGlmIChfX0RFVl9fKSB7XG4gICAgICB2YXIgdHIgPSB0aGlzLmdldEN1cnJlbnRUcmFuc2FjdGlvbigpO1xuICAgICAgdHIgJiYgdGhpcy5fbG9nZ2VyLmRlYnVnKFwiZW5kU3BhbihcIiArIHNwYW4ubmFtZSArIFwiLCBcIiArIHNwYW4udHlwZSArIFwiKVwiLCBcIm9uIHRyYW5zYWN0aW9uKFwiICsgdHIuaWQgKyBcIiwgXCIgKyB0ci5uYW1lICsgXCIpXCIpO1xuICAgIH1cblxuICAgIHNwYW4uZW5kKG51bGwsIGNvbnRleHQpO1xuICB9O1xuXG4gIHJldHVybiBUcmFuc2FjdGlvblNlcnZpY2U7XG59KCk7XG5cbmV4cG9ydCBkZWZhdWx0IFRyYW5zYWN0aW9uU2VydmljZTsiLCJmdW5jdGlvbiBfaW5oZXJpdHNMb29zZShzdWJDbGFzcywgc3VwZXJDbGFzcykgeyBzdWJDbGFzcy5wcm90b3R5cGUgPSBPYmplY3QuY3JlYXRlKHN1cGVyQ2xhc3MucHJvdG90eXBlKTsgc3ViQ2xhc3MucHJvdG90eXBlLmNvbnN0cnVjdG9yID0gc3ViQ2xhc3M7IF9zZXRQcm90b3R5cGVPZihzdWJDbGFzcywgc3VwZXJDbGFzcyk7IH1cblxuZnVuY3Rpb24gX3NldFByb3RvdHlwZU9mKG8sIHApIHsgX3NldFByb3RvdHlwZU9mID0gT2JqZWN0LnNldFByb3RvdHlwZU9mIHx8IGZ1bmN0aW9uIF9zZXRQcm90b3R5cGVPZihvLCBwKSB7IG8uX19wcm90b19fID0gcDsgcmV0dXJuIG87IH07IHJldHVybiBfc2V0UHJvdG90eXBlT2YobywgcCk7IH1cblxuaW1wb3J0IFNwYW4gZnJvbSAnLi9zcGFuJztcbmltcG9ydCBTcGFuQmFzZSBmcm9tICcuL3NwYW4tYmFzZSc7XG5pbXBvcnQgeyBnZW5lcmF0ZVJhbmRvbUlkLCBtZXJnZSwgbm93LCBnZXRUaW1lLCBleHRlbmQsIHJlbW92ZUludmFsaWRDaGFycyB9IGZyb20gJy4uL2NvbW1vbi91dGlscyc7XG5pbXBvcnQgeyBSRVVTQUJJTElUWV9USFJFU0hPTEQsIFRSVU5DQVRFRF9UWVBFIH0gZnJvbSAnLi4vY29tbW9uL2NvbnN0YW50cyc7XG5pbXBvcnQgeyBjYXB0dXJlQnJlYWtkb3duIGFzIF9jYXB0dXJlQnJlYWtkb3duIH0gZnJvbSAnLi9icmVha2Rvd24nO1xuXG52YXIgVHJhbnNhY3Rpb24gPSBmdW5jdGlvbiAoX1NwYW5CYXNlKSB7XG4gIF9pbmhlcml0c0xvb3NlKFRyYW5zYWN0aW9uLCBfU3BhbkJhc2UpO1xuXG4gIGZ1bmN0aW9uIFRyYW5zYWN0aW9uKG5hbWUsIHR5cGUsIG9wdGlvbnMpIHtcbiAgICB2YXIgX3RoaXM7XG5cbiAgICBfdGhpcyA9IF9TcGFuQmFzZS5jYWxsKHRoaXMsIG5hbWUsIHR5cGUsIG9wdGlvbnMpIHx8IHRoaXM7XG4gICAgX3RoaXMudHJhY2VJZCA9IGdlbmVyYXRlUmFuZG9tSWQoKTtcbiAgICBfdGhpcy5tYXJrcyA9IHVuZGVmaW5lZDtcbiAgICBfdGhpcy5zcGFucyA9IFtdO1xuICAgIF90aGlzLl9hY3RpdmVTcGFucyA9IHt9O1xuICAgIF90aGlzLl9hY3RpdmVUYXNrcyA9IG5ldyBTZXQoKTtcbiAgICBfdGhpcy5ibG9ja2VkID0gZmFsc2U7XG4gICAgX3RoaXMuY2FwdHVyZVRpbWluZ3MgPSBmYWxzZTtcbiAgICBfdGhpcy5icmVha2Rvd25UaW1pbmdzID0gW107XG4gICAgX3RoaXMuc2FtcGxlUmF0ZSA9IF90aGlzLm9wdGlvbnMudHJhbnNhY3Rpb25TYW1wbGVSYXRlO1xuICAgIF90aGlzLnNhbXBsZWQgPSBNYXRoLnJhbmRvbSgpIDw9IF90aGlzLnNhbXBsZVJhdGU7XG4gICAgcmV0dXJuIF90aGlzO1xuICB9XG5cbiAgdmFyIF9wcm90byA9IFRyYW5zYWN0aW9uLnByb3RvdHlwZTtcblxuICBfcHJvdG8uYWRkTWFya3MgPSBmdW5jdGlvbiBhZGRNYXJrcyhvYmopIHtcbiAgICB0aGlzLm1hcmtzID0gbWVyZ2UodGhpcy5tYXJrcyB8fCB7fSwgb2JqKTtcbiAgfTtcblxuICBfcHJvdG8ubWFyayA9IGZ1bmN0aW9uIG1hcmsoa2V5KSB7XG4gICAgdmFyIHNrZXkgPSByZW1vdmVJbnZhbGlkQ2hhcnMoa2V5KTtcblxuICAgIHZhciBtYXJrVGltZSA9IG5vdygpIC0gdGhpcy5fc3RhcnQ7XG5cbiAgICB2YXIgY3VzdG9tID0ge307XG4gICAgY3VzdG9tW3NrZXldID0gbWFya1RpbWU7XG4gICAgdGhpcy5hZGRNYXJrcyh7XG4gICAgICBjdXN0b206IGN1c3RvbVxuICAgIH0pO1xuICB9O1xuXG4gIF9wcm90by5jYW5SZXVzZSA9IGZ1bmN0aW9uIGNhblJldXNlKCkge1xuICAgIHZhciB0aHJlc2hvbGQgPSB0aGlzLm9wdGlvbnMucmV1c2VUaHJlc2hvbGQgfHwgUkVVU0FCSUxJVFlfVEhSRVNIT0xEO1xuICAgIHJldHVybiAhIXRoaXMub3B0aW9ucy5jYW5SZXVzZSAmJiAhdGhpcy5lbmRlZCAmJiBub3coKSAtIHRoaXMuX3N0YXJ0IDwgdGhyZXNob2xkO1xuICB9O1xuXG4gIF9wcm90by5yZWRlZmluZSA9IGZ1bmN0aW9uIHJlZGVmaW5lKG5hbWUsIHR5cGUsIG9wdGlvbnMpIHtcbiAgICBpZiAobmFtZSkge1xuICAgICAgdGhpcy5uYW1lID0gbmFtZTtcbiAgICB9XG5cbiAgICBpZiAodHlwZSkge1xuICAgICAgdGhpcy50eXBlID0gdHlwZTtcbiAgICB9XG5cbiAgICBpZiAob3B0aW9ucykge1xuICAgICAgdGhpcy5vcHRpb25zLnJldXNlVGhyZXNob2xkID0gb3B0aW9ucy5yZXVzZVRocmVzaG9sZDtcbiAgICAgIGV4dGVuZCh0aGlzLm9wdGlvbnMsIG9wdGlvbnMpO1xuICAgIH1cbiAgfTtcblxuICBfcHJvdG8uc3RhcnRTcGFuID0gZnVuY3Rpb24gc3RhcnRTcGFuKG5hbWUsIHR5cGUsIG9wdGlvbnMpIHtcbiAgICB2YXIgX3RoaXMyID0gdGhpcztcblxuICAgIGlmICh0aGlzLmVuZGVkKSB7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgdmFyIG9wdHMgPSBleHRlbmQoe30sIG9wdGlvbnMpO1xuXG4gICAgb3B0cy5vbkVuZCA9IGZ1bmN0aW9uICh0cmMpIHtcbiAgICAgIF90aGlzMi5fb25TcGFuRW5kKHRyYyk7XG4gICAgfTtcblxuICAgIG9wdHMudHJhY2VJZCA9IHRoaXMudHJhY2VJZDtcbiAgICBvcHRzLnNhbXBsZWQgPSB0aGlzLnNhbXBsZWQ7XG4gICAgb3B0cy5zYW1wbGVSYXRlID0gdGhpcy5zYW1wbGVSYXRlO1xuXG4gICAgaWYgKCFvcHRzLnBhcmVudElkKSB7XG4gICAgICBvcHRzLnBhcmVudElkID0gdGhpcy5pZDtcbiAgICB9XG5cbiAgICB2YXIgc3BhbiA9IG5ldyBTcGFuKG5hbWUsIHR5cGUsIG9wdHMpO1xuICAgIHRoaXMuX2FjdGl2ZVNwYW5zW3NwYW4uaWRdID0gc3BhbjtcblxuICAgIGlmIChvcHRzLmJsb2NraW5nKSB7XG4gICAgICB0aGlzLmFkZFRhc2soc3Bhbi5pZCk7XG4gICAgfVxuXG4gICAgcmV0dXJuIHNwYW47XG4gIH07XG5cbiAgX3Byb3RvLmlzRmluaXNoZWQgPSBmdW5jdGlvbiBpc0ZpbmlzaGVkKCkge1xuICAgIHJldHVybiAhdGhpcy5ibG9ja2VkICYmIHRoaXMuX2FjdGl2ZVRhc2tzLnNpemUgPT09IDA7XG4gIH07XG5cbiAgX3Byb3RvLmRldGVjdEZpbmlzaCA9IGZ1bmN0aW9uIGRldGVjdEZpbmlzaCgpIHtcbiAgICBpZiAodGhpcy5pc0ZpbmlzaGVkKCkpIHRoaXMuZW5kKCk7XG4gIH07XG5cbiAgX3Byb3RvLmVuZCA9IGZ1bmN0aW9uIGVuZChlbmRUaW1lKSB7XG4gICAgaWYgKHRoaXMuZW5kZWQpIHtcbiAgICAgIHJldHVybjtcbiAgICB9XG5cbiAgICB0aGlzLmVuZGVkID0gdHJ1ZTtcbiAgICB0aGlzLl9lbmQgPSBnZXRUaW1lKGVuZFRpbWUpO1xuXG4gICAgZm9yICh2YXIgc2lkIGluIHRoaXMuX2FjdGl2ZVNwYW5zKSB7XG4gICAgICB2YXIgc3BhbiA9IHRoaXMuX2FjdGl2ZVNwYW5zW3NpZF07XG4gICAgICBzcGFuLnR5cGUgPSBzcGFuLnR5cGUgKyBUUlVOQ0FURURfVFlQRTtcbiAgICAgIHNwYW4uZW5kKGVuZFRpbWUpO1xuICAgIH1cblxuICAgIHRoaXMuY2FsbE9uRW5kKCk7XG4gIH07XG5cbiAgX3Byb3RvLmNhcHR1cmVCcmVha2Rvd24gPSBmdW5jdGlvbiBjYXB0dXJlQnJlYWtkb3duKCkge1xuICAgIHRoaXMuYnJlYWtkb3duVGltaW5ncyA9IF9jYXB0dXJlQnJlYWtkb3duKHRoaXMpO1xuICB9O1xuXG4gIF9wcm90by5ibG9jayA9IGZ1bmN0aW9uIGJsb2NrKGZsYWcpIHtcbiAgICB0aGlzLmJsb2NrZWQgPSBmbGFnO1xuXG4gICAgaWYgKCF0aGlzLmJsb2NrZWQpIHtcbiAgICAgIHRoaXMuZGV0ZWN0RmluaXNoKCk7XG4gICAgfVxuICB9O1xuXG4gIF9wcm90by5hZGRUYXNrID0gZnVuY3Rpb24gYWRkVGFzayh0YXNrSWQpIHtcbiAgICBpZiAoIXRhc2tJZCkge1xuICAgICAgdGFza0lkID0gJ3Rhc2stJyArIGdlbmVyYXRlUmFuZG9tSWQoMTYpO1xuICAgIH1cblxuICAgIHRoaXMuX2FjdGl2ZVRhc2tzLmFkZCh0YXNrSWQpO1xuXG4gICAgcmV0dXJuIHRhc2tJZDtcbiAgfTtcblxuICBfcHJvdG8ucmVtb3ZlVGFzayA9IGZ1bmN0aW9uIHJlbW92ZVRhc2sodGFza0lkKSB7XG4gICAgdmFyIGRlbGV0ZWQgPSB0aGlzLl9hY3RpdmVUYXNrcy5kZWxldGUodGFza0lkKTtcblxuICAgIGRlbGV0ZWQgJiYgdGhpcy5kZXRlY3RGaW5pc2goKTtcbiAgfTtcblxuICBfcHJvdG8ucmVzZXRGaWVsZHMgPSBmdW5jdGlvbiByZXNldEZpZWxkcygpIHtcbiAgICB0aGlzLnNwYW5zID0gW107XG4gICAgdGhpcy5zYW1wbGVSYXRlID0gMDtcbiAgfTtcblxuICBfcHJvdG8uX29uU3BhbkVuZCA9IGZ1bmN0aW9uIF9vblNwYW5FbmQoc3Bhbikge1xuICAgIHRoaXMuc3BhbnMucHVzaChzcGFuKTtcbiAgICBkZWxldGUgdGhpcy5fYWN0aXZlU3BhbnNbc3Bhbi5pZF07XG4gICAgdGhpcy5yZW1vdmVUYXNrKHNwYW4uaWQpO1xuICB9O1xuXG4gIF9wcm90by5pc01hbmFnZWQgPSBmdW5jdGlvbiBpc01hbmFnZWQoKSB7XG4gICAgcmV0dXJuICEhdGhpcy5vcHRpb25zLm1hbmFnZWQ7XG4gIH07XG5cbiAgcmV0dXJuIFRyYW5zYWN0aW9uO1xufShTcGFuQmFzZSk7XG5cbmV4cG9ydCBkZWZhdWx0IFRyYW5zYWN0aW9uOyIsInZhciBfX0RFVl9fID0gcHJvY2Vzcy5lbnYuTk9ERV9FTlYgIT09ICdwcm9kdWN0aW9uJztcblxudmFyIHN0YXRlID0ge1xuICBib290c3RyYXBUaW1lOiBudWxsLFxuICBsYXN0SGlkZGVuU3RhcnQ6IE51bWJlci5NSU5fU0FGRV9JTlRFR0VSXG59O1xuZXhwb3J0IHsgX19ERVZfXywgc3RhdGUgfTsiLCIvKipcbiAqIE1JVCBMaWNlbnNlXG4gKlxuICogQ29weXJpZ2h0IChjKSAyMDE3LXByZXNlbnQsIEVsYXN0aWNzZWFyY2ggQlZcbiAqXG4gKiBQZXJtaXNzaW9uIGlzIGhlcmVieSBncmFudGVkLCBmcmVlIG9mIGNoYXJnZSwgdG8gYW55IHBlcnNvbiBvYnRhaW5pbmcgYSBjb3B5XG4gKiBvZiB0aGlzIHNvZnR3YXJlIGFuZCBhc3NvY2lhdGVkIGRvY3VtZW50YXRpb24gZmlsZXMgKHRoZSBcIlNvZnR3YXJlXCIpLCB0byBkZWFsXG4gKiBpbiB0aGUgU29mdHdhcmUgd2l0aG91dCByZXN0cmljdGlvbiwgaW5jbHVkaW5nIHdpdGhvdXQgbGltaXRhdGlvbiB0aGUgcmlnaHRzXG4gKiB0byB1c2UsIGNvcHksIG1vZGlmeSwgbWVyZ2UsIHB1Ymxpc2gsIGRpc3RyaWJ1dGUsIHN1YmxpY2Vuc2UsIGFuZC9vciBzZWxsXG4gKiBjb3BpZXMgb2YgdGhlIFNvZnR3YXJlLCBhbmQgdG8gcGVybWl0IHBlcnNvbnMgdG8gd2hvbSB0aGUgU29mdHdhcmUgaXNcbiAqIGZ1cm5pc2hlZCB0byBkbyBzbywgc3ViamVjdCB0byB0aGUgZm9sbG93aW5nIGNvbmRpdGlvbnM6XG4gKlxuICogVGhlIGFib3ZlIGNvcHlyaWdodCBub3RpY2UgYW5kIHRoaXMgcGVybWlzc2lvbiBub3RpY2Ugc2hhbGwgYmUgaW5jbHVkZWQgaW5cbiAqIGFsbCBjb3BpZXMgb3Igc3Vic3RhbnRpYWwgcG9ydGlvbnMgb2YgdGhlIFNvZnR3YXJlLlxuICpcbiAqIFRIRSBTT0ZUV0FSRSBJUyBQUk9WSURFRCBcIkFTIElTXCIsIFdJVEhPVVQgV0FSUkFOVFkgT0YgQU5ZIEtJTkQsIEVYUFJFU1MgT1JcbiAqIElNUExJRUQsIElOQ0xVRElORyBCVVQgTk9UIExJTUlURUQgVE8gVEhFIFdBUlJBTlRJRVMgT0YgTUVSQ0hBTlRBQklMSVRZLFxuICogRklUTkVTUyBGT1IgQSBQQVJUSUNVTEFSIFBVUlBPU0UgQU5EIE5PTklORlJJTkdFTUVOVC4gSU4gTk8gRVZFTlQgU0hBTEwgVEhFXG4gKiBBVVRIT1JTIE9SIENPUFlSSUdIVCBIT0xERVJTIEJFIExJQUJMRSBGT1IgQU5ZIENMQUlNLCBEQU1BR0VTIE9SIE9USEVSXG4gKiBMSUFCSUxJVFksIFdIRVRIRVIgSU4gQU4gQUNUSU9OIE9GIENPTlRSQUNULCBUT1JUIE9SIE9USEVSV0lTRSwgQVJJU0lORyBGUk9NLFxuICogT1VUIE9GIE9SIElOIENPTk5FQ1RJT04gV0lUSCBUSEUgU09GVFdBUkUgT1IgVEhFIFVTRSBPUiBPVEhFUiBERUFMSU5HUyBJTlxuICogVEhFIFNPRlRXQVJFLlxuICpcbiAqL1xuXG5pbXBvcnQge1xuICBnZXRJbnN0cnVtZW50YXRpb25GbGFncyxcbiAgUEFHRV9MT0FEX0RFTEFZLFxuICBQQUdFX0xPQUQsXG4gIEVSUk9SLFxuICBDT05GSUdfU0VSVklDRSxcbiAgTE9HR0lOR19TRVJWSUNFLFxuICBUUkFOU0FDVElPTl9TRVJWSUNFLFxuICBQRVJGT1JNQU5DRV9NT05JVE9SSU5HLFxuICBFUlJPUl9MT0dHSU5HLFxuICBBUE1fU0VSVkVSLFxuICBFVkVOVF9UQVJHRVQsXG4gIENMSUNLLFxuICBvYnNlcnZlUGFnZVZpc2liaWxpdHksXG4gIG9ic2VydmVQYWdlQ2xpY2tzXG59IGZyb20gJ0BlbGFzdGljL2FwbS1ydW0tY29yZSdcblxuZXhwb3J0IGRlZmF1bHQgY2xhc3MgQXBtQmFzZSB7XG4gIGNvbnN0cnVjdG9yKHNlcnZpY2VGYWN0b3J5LCBkaXNhYmxlKSB7XG4gICAgdGhpcy5fZGlzYWJsZSA9IGRpc2FibGVcbiAgICB0aGlzLnNlcnZpY2VGYWN0b3J5ID0gc2VydmljZUZhY3RvcnlcbiAgICB0aGlzLl9pbml0aWFsaXplZCA9IGZhbHNlXG4gIH1cblxuICBpc0VuYWJsZWQoKSB7XG4gICAgcmV0dXJuICF0aGlzLl9kaXNhYmxlXG4gIH1cblxuICBpc0FjdGl2ZSgpIHtcbiAgICBjb25zdCBjb25maWdTZXJ2aWNlID0gdGhpcy5zZXJ2aWNlRmFjdG9yeS5nZXRTZXJ2aWNlKENPTkZJR19TRVJWSUNFKVxuICAgIHJldHVybiB0aGlzLmlzRW5hYmxlZCgpICYmIHRoaXMuX2luaXRpYWxpemVkICYmIGNvbmZpZ1NlcnZpY2UuZ2V0KCdhY3RpdmUnKVxuICB9XG5cbiAgaW5pdChjb25maWcpIHtcbiAgICBpZiAodGhpcy5pc0VuYWJsZWQoKSAmJiAhdGhpcy5faW5pdGlhbGl6ZWQpIHtcbiAgICAgIHRoaXMuX2luaXRpYWxpemVkID0gdHJ1ZVxuICAgICAgY29uc3QgW1xuICAgICAgICBjb25maWdTZXJ2aWNlLFxuICAgICAgICBsb2dnaW5nU2VydmljZSxcbiAgICAgICAgdHJhbnNhY3Rpb25TZXJ2aWNlXG4gICAgICBdID0gdGhpcy5zZXJ2aWNlRmFjdG9yeS5nZXRTZXJ2aWNlKFtcbiAgICAgICAgQ09ORklHX1NFUlZJQ0UsXG4gICAgICAgIExPR0dJTkdfU0VSVklDRSxcbiAgICAgICAgVFJBTlNBQ1RJT05fU0VSVklDRVxuICAgICAgXSlcbiAgICAgIC8qKlxuICAgICAgICogU2V0IEFnZW50IHZlcnNpb24gdG8gYmUgc2VudCBhcyBwYXJ0IG9mIG1ldGFkYXRhIHRvIHRoZSBBUE0gU2VydmVyXG4gICAgICAgKi9cbiAgICAgIGNvbmZpZ1NlcnZpY2Uuc2V0VmVyc2lvbignNS4xMi4wJylcbiAgICAgIHRoaXMuY29uZmlnKGNvbmZpZylcbiAgICAgIC8qKlxuICAgICAgICogU2V0IGxldmVsIGhlcmUgdG8gYWNjb3VudCBmb3IgYm90aCBhY3RpdmUgYW5kIGluYWN0aXZlIGNhc2VzXG4gICAgICAgKi9cbiAgICAgIGNvbnN0IGxvZ0xldmVsID0gY29uZmlnU2VydmljZS5nZXQoJ2xvZ0xldmVsJylcbiAgICAgIGxvZ2dpbmdTZXJ2aWNlLnNldExldmVsKGxvZ0xldmVsKVxuICAgICAgLyoqXG4gICAgICAgKiBEZWFjdGl2ZSBhZ2VudCB3aGVuIHRoZSBhY3RpdmUgY29uZmlnIGZsYWcgaXMgc2V0IHRvIGZhbHNlXG4gICAgICAgKi9cbiAgICAgIGNvbnN0IGlzQ29uZmlnQWN0aXZlID0gY29uZmlnU2VydmljZS5nZXQoJ2FjdGl2ZScpXG4gICAgICBpZiAoaXNDb25maWdBY3RpdmUpIHtcbiAgICAgICAgdGhpcy5zZXJ2aWNlRmFjdG9yeS5pbml0KClcblxuICAgICAgICBjb25zdCBmbGFncyA9IGdldEluc3RydW1lbnRhdGlvbkZsYWdzKFxuICAgICAgICAgIGNvbmZpZ1NlcnZpY2UuZ2V0KCdpbnN0cnVtZW50JyksXG4gICAgICAgICAgY29uZmlnU2VydmljZS5nZXQoJ2Rpc2FibGVJbnN0cnVtZW50YXRpb25zJylcbiAgICAgICAgKVxuXG4gICAgICAgIGNvbnN0IHBlcmZvcm1hbmNlTW9uaXRvcmluZyA9IHRoaXMuc2VydmljZUZhY3RvcnkuZ2V0U2VydmljZShcbiAgICAgICAgICBQRVJGT1JNQU5DRV9NT05JVE9SSU5HXG4gICAgICAgIClcbiAgICAgICAgcGVyZm9ybWFuY2VNb25pdG9yaW5nLmluaXQoZmxhZ3MpXG5cbiAgICAgICAgaWYgKGZsYWdzW0VSUk9SXSkge1xuICAgICAgICAgIGNvbnN0IGVycm9yTG9nZ2luZyA9IHRoaXMuc2VydmljZUZhY3RvcnkuZ2V0U2VydmljZShFUlJPUl9MT0dHSU5HKVxuICAgICAgICAgIGVycm9yTG9nZ2luZy5yZWdpc3Rlckxpc3RlbmVycygpXG4gICAgICAgIH1cblxuICAgICAgICBpZiAoY29uZmlnU2VydmljZS5nZXQoJ3Nlc3Npb24nKSkge1xuICAgICAgICAgIGxldCBsb2NhbENvbmZpZyA9IGNvbmZpZ1NlcnZpY2UuZ2V0TG9jYWxDb25maWcoKVxuICAgICAgICAgIGlmIChsb2NhbENvbmZpZyAmJiBsb2NhbENvbmZpZy5zZXNzaW9uKSB7XG4gICAgICAgICAgICBjb25maWdTZXJ2aWNlLnNldENvbmZpZyh7XG4gICAgICAgICAgICAgIHNlc3Npb246IGxvY2FsQ29uZmlnLnNlc3Npb25cbiAgICAgICAgICAgIH0pXG4gICAgICAgICAgfVxuICAgICAgICB9XG5cbiAgICAgICAgY29uc3Qgc2VuZFBhZ2VMb2FkID0gKCkgPT5cbiAgICAgICAgICBmbGFnc1tQQUdFX0xPQURdICYmIHRoaXMuX3NlbmRQYWdlTG9hZE1ldHJpY3MoKVxuXG4gICAgICAgIGlmIChjb25maWdTZXJ2aWNlLmdldCgnY2VudHJhbENvbmZpZycpKSB7XG4gICAgICAgICAgLyoqXG4gICAgICAgICAgICogV2FpdGluZyBmb3IgdGhlIHJlbW90ZSBjb25maWcgYmVmb3JlIHNlbmRpbmcgdGhlIHBhZ2UgbG9hZCB0cmFuc2FjdGlvblxuICAgICAgICAgICAqL1xuICAgICAgICAgIHRoaXMuZmV0Y2hDZW50cmFsQ29uZmlnKCkudGhlbihzZW5kUGFnZUxvYWQpXG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgc2VuZFBhZ2VMb2FkKClcbiAgICAgICAgfVxuXG4gICAgICAgIG9ic2VydmVQYWdlVmlzaWJpbGl0eShjb25maWdTZXJ2aWNlLCB0cmFuc2FjdGlvblNlcnZpY2UpXG4gICAgICAgIGlmIChmbGFnc1tFVkVOVF9UQVJHRVRdICYmIGZsYWdzW0NMSUNLXSkge1xuICAgICAgICAgIG9ic2VydmVQYWdlQ2xpY2tzKHRyYW5zYWN0aW9uU2VydmljZSlcbiAgICAgICAgfVxuICAgICAgfSBlbHNlIHtcbiAgICAgICAgdGhpcy5fZGlzYWJsZSA9IHRydWVcbiAgICAgICAgbG9nZ2luZ1NlcnZpY2Uud2FybignUlVNIGFnZW50IGlzIGluYWN0aXZlJylcbiAgICAgIH1cbiAgICB9XG4gICAgcmV0dXJuIHRoaXNcbiAgfVxuXG4gIC8qKlxuICAgKiBgZmV0Y2hDZW50cmFsQ29uZmlnYCByZXR1cm5zIGEgcHJvbWlzZSB0aGF0IHdpbGwgYWx3YXlzIHJlc29sdmVcbiAgICogaWYgdGhlIGludGVybmFsIGNvbmZpZyBmZXRjaCBmYWlscyB0aGUgdGhlIHByb21pc2UgcmVzb2x2ZXMgdG8gYHVuZGVmaW5lZGAgb3RoZXJ3aXNlXG4gICAqIGl0IHJlc29sdmVzIHRvIHRoZSBmZXRjaGVkIGNvbmZpZy5cbiAgICovXG4gIGZldGNoQ2VudHJhbENvbmZpZygpIHtcbiAgICBjb25zdCBbXG4gICAgICBhcG1TZXJ2ZXIsXG4gICAgICBsb2dnaW5nU2VydmljZSxcbiAgICAgIGNvbmZpZ1NlcnZpY2VcbiAgICBdID0gdGhpcy5zZXJ2aWNlRmFjdG9yeS5nZXRTZXJ2aWNlKFtcbiAgICAgIEFQTV9TRVJWRVIsXG4gICAgICBMT0dHSU5HX1NFUlZJQ0UsXG4gICAgICBDT05GSUdfU0VSVklDRVxuICAgIF0pXG5cbiAgICByZXR1cm4gYXBtU2VydmVyXG4gICAgICAuZmV0Y2hDb25maWcoXG4gICAgICAgIGNvbmZpZ1NlcnZpY2UuZ2V0KCdzZXJ2aWNlTmFtZScpLFxuICAgICAgICBjb25maWdTZXJ2aWNlLmdldCgnZW52aXJvbm1lbnQnKVxuICAgICAgKVxuICAgICAgLnRoZW4oY29uZmlnID0+IHtcbiAgICAgICAgdmFyIHRyYW5zYWN0aW9uU2FtcGxlUmF0ZSA9IGNvbmZpZ1sndHJhbnNhY3Rpb25fc2FtcGxlX3JhdGUnXVxuICAgICAgICBpZiAodHJhbnNhY3Rpb25TYW1wbGVSYXRlKSB7XG4gICAgICAgICAgdHJhbnNhY3Rpb25TYW1wbGVSYXRlID0gTnVtYmVyKHRyYW5zYWN0aW9uU2FtcGxlUmF0ZSlcbiAgICAgICAgICBjb25zdCBjb25maWcgPSB7IHRyYW5zYWN0aW9uU2FtcGxlUmF0ZSB9XG4gICAgICAgICAgY29uc3QgeyBpbnZhbGlkIH0gPSBjb25maWdTZXJ2aWNlLnZhbGlkYXRlKGNvbmZpZylcbiAgICAgICAgICBpZiAoaW52YWxpZC5sZW5ndGggPT09IDApIHtcbiAgICAgICAgICAgIGNvbmZpZ1NlcnZpY2Uuc2V0Q29uZmlnKGNvbmZpZylcbiAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgY29uc3QgeyBrZXksIHZhbHVlLCBhbGxvd2VkIH0gPSBpbnZhbGlkWzBdXG4gICAgICAgICAgICBsb2dnaW5nU2VydmljZS53YXJuKFxuICAgICAgICAgICAgICBgaW52YWxpZCB2YWx1ZSBcIiR7dmFsdWV9XCIgZm9yICR7a2V5fS4gQWxsb3dlZDogJHthbGxvd2VkfS5gXG4gICAgICAgICAgICApXG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICAgIHJldHVybiBjb25maWdcbiAgICAgIH0pXG4gICAgICAuY2F0Y2goZXJyb3IgPT4ge1xuICAgICAgICBsb2dnaW5nU2VydmljZS53YXJuKCdmYWlsZWQgZmV0Y2hpbmcgY29uZmlnOicsIGVycm9yKVxuICAgICAgfSlcbiAgfVxuXG4gIF9zZW5kUGFnZUxvYWRNZXRyaWNzKCkge1xuICAgIC8qKlxuICAgICAqIE5hbWUgb2YgdGhlIHRyYW5zYWN0aW9uIGlzIHNldCBpbiB0cmFuc2FjdGlvbiBzZXJ2aWNlIHRvXG4gICAgICogYXZvaWQgZHVwbGljYXRpbmcgdGhlIGxvZ2ljIGF0IG11bHRpcGxlIHBsYWNlc1xuICAgICAqL1xuICAgIGNvbnN0IHRyID0gdGhpcy5zdGFydFRyYW5zYWN0aW9uKHVuZGVmaW5lZCwgUEFHRV9MT0FELCB7XG4gICAgICBtYW5hZ2VkOiB0cnVlLFxuICAgICAgY2FuUmV1c2U6IHRydWVcbiAgICB9KVxuXG4gICAgaWYgKCF0cikge1xuICAgICAgcmV0dXJuXG4gICAgfVxuXG4gICAgdHIuYWRkVGFzayhQQUdFX0xPQUQpXG4gICAgY29uc3Qgc2VuZFBhZ2VMb2FkTWV0cmljcyA9ICgpID0+IHtcbiAgICAgIC8vIFRoZSByZWFzb25zIG9mIHRoaXMgdGltZW91dCBhcmU6XG4gICAgICAvLyAxLiB0byBtYWtlIHN1cmUgUGVyZm9ybWFuY2VUaW1pbmcubG9hZEV2ZW50RW5kIGhhcyBhIHZhbHVlLlxuICAgICAgLy8gMi4gdG8gbWFrZSBzdXJlIHRoZSBhZ2VudCBpbnRlcmNlcHRzIGFsbCB0aGUgTENQIGVudHJpZXMgdHJpZ2dlcmVkIGJ5IHRoZSBicm93c2VyIChhZGRpbmcgYSBkZWxheSBpbiB0aGUgdGltZW91dCkuXG4gICAgICAvLyBUaGUgYnJvd3NlciBtaWdodCBuZWVkIG1vcmUgdGltZSBhZnRlciB0aGUgcGFnZWxvYWQgZXZlbnQgdG8gcmVuZGVyIG90aGVyIGVsZW1lbnRzIChlLmcuIGltYWdlcykuXG4gICAgICAvLyBUaGF0J3MgaW1wb3J0YW50IGJlY2F1c2UgYSBMQ1AgaXMgb25seSB0cmlnZ2VyZWQgd2hlbiB0aGUgcmVsYXRlZCBlbGVtZW50IGlzIGNvbXBsZXRlbHkgcmVuZGVyZWQuXG4gICAgICAvLyBodHRwczovL3czYy5naXRodWIuaW8vbGFyZ2VzdC1jb250ZW50ZnVsLXBhaW50LyNzZWMtYWRkLWxjcC1lbnRyeVxuICAgICAgc2V0VGltZW91dCgoKSA9PiB0ci5yZW1vdmVUYXNrKFBBR0VfTE9BRCksIFBBR0VfTE9BRF9ERUxBWSlcbiAgICB9XG5cbiAgICBpZiAoZG9jdW1lbnQucmVhZHlTdGF0ZSA9PT0gJ2NvbXBsZXRlJykge1xuICAgICAgc2VuZFBhZ2VMb2FkTWV0cmljcygpXG4gICAgfSBlbHNlIHtcbiAgICAgIHdpbmRvdy5hZGRFdmVudExpc3RlbmVyKCdsb2FkJywgc2VuZFBhZ2VMb2FkTWV0cmljcylcbiAgICB9XG4gIH1cblxuICBvYnNlcnZlKG5hbWUsIGZuKSB7XG4gICAgY29uc3QgY29uZmlnU2VydmljZSA9IHRoaXMuc2VydmljZUZhY3RvcnkuZ2V0U2VydmljZShDT05GSUdfU0VSVklDRSlcbiAgICBjb25maWdTZXJ2aWNlLmV2ZW50cy5vYnNlcnZlKG5hbWUsIGZuKVxuICB9XG5cbiAgLyoqXG4gICAqIFdoZW4gdGhlIHJlcXVpcmVkIGNvbmZpZyBrZXlzIGFyZSBpbnZhbGlkLCB0aGUgYWdlbnQgaXMgZGVhY3RpdmF0ZWQgd2l0aFxuICAgKiBsb2dnaW5nIGVycm9yIHRvIHRoZSBjb25zb2xlXG4gICAqXG4gICAqIHZhbGlkYXRpb24gZXJyb3IgZm9ybWF0XG4gICAqIHtcbiAgICogIG1pc3Npbmc6IFsgJ2tleTEnLCAna2V5MiddLFxuICAgKiAgaW52YWxpZDogW3tcbiAgICogICAga2V5OiAnYScsXG4gICAqICAgIHZhbHVlOiAnYWJjZCcsXG4gICAqICAgIGFsbG93ZWQ6ICdzdHJpbmcnXG4gICAqICB9XSxcbiAgICogIHVua25vd246IFsna2V5MycsICdrZXk0J11cbiAgICogfVxuICAgKi9cbiAgY29uZmlnKGNvbmZpZykge1xuICAgIGNvbnN0IFtjb25maWdTZXJ2aWNlLCBsb2dnaW5nU2VydmljZV0gPSB0aGlzLnNlcnZpY2VGYWN0b3J5LmdldFNlcnZpY2UoW1xuICAgICAgQ09ORklHX1NFUlZJQ0UsXG4gICAgICBMT0dHSU5HX1NFUlZJQ0VcbiAgICBdKVxuICAgIGNvbnN0IHsgbWlzc2luZywgaW52YWxpZCwgdW5rbm93biB9ID0gY29uZmlnU2VydmljZS52YWxpZGF0ZShjb25maWcpXG4gICAgaWYgKHVua25vd24ubGVuZ3RoID4gMCkge1xuICAgICAgY29uc3QgbWVzc2FnZSA9XG4gICAgICAgICdVbmtub3duIGNvbmZpZyBvcHRpb25zIGFyZSBzcGVjaWZpZWQgZm9yIFJVTSBhZ2VudDogJyArXG4gICAgICAgIHVua25vd24uam9pbignLCAnKVxuICAgICAgbG9nZ2luZ1NlcnZpY2Uud2FybihtZXNzYWdlKVxuICAgIH1cblxuICAgIGlmIChtaXNzaW5nLmxlbmd0aCA9PT0gMCAmJiBpbnZhbGlkLmxlbmd0aCA9PT0gMCkge1xuICAgICAgY29uZmlnU2VydmljZS5zZXRDb25maWcoY29uZmlnKVxuICAgIH0gZWxzZSB7XG4gICAgICBjb25zdCBzZXBhcmF0b3IgPSAnLCAnXG4gICAgICBsZXQgbWVzc2FnZSA9IFwiUlVNIGFnZW50IGlzbid0IGNvcnJlY3RseSBjb25maWd1cmVkLiBcIlxuXG4gICAgICBpZiAobWlzc2luZy5sZW5ndGggPiAwKSB7XG4gICAgICAgIG1lc3NhZ2UgKz0gbWlzc2luZy5qb2luKHNlcGFyYXRvcikgKyAnIGlzIG1pc3NpbmcnXG4gICAgICAgIGlmIChpbnZhbGlkLmxlbmd0aCA+IDApIHtcbiAgICAgICAgICBtZXNzYWdlICs9IHNlcGFyYXRvclxuICAgICAgICB9XG4gICAgICB9XG5cbiAgICAgIGludmFsaWQuZm9yRWFjaCgoeyBrZXksIHZhbHVlLCBhbGxvd2VkIH0sIGluZGV4KSA9PiB7XG4gICAgICAgIG1lc3NhZ2UgKz1cbiAgICAgICAgICBgJHtrZXl9IFwiJHt2YWx1ZX1cIiBjb250YWlucyBpbnZhbGlkIGNoYXJhY3RlcnMhIChhbGxvd2VkOiAke2FsbG93ZWR9KWAgK1xuICAgICAgICAgIChpbmRleCAhPT0gaW52YWxpZC5sZW5ndGggLSAxID8gc2VwYXJhdG9yIDogJycpXG4gICAgICB9KVxuICAgICAgbG9nZ2luZ1NlcnZpY2UuZXJyb3IobWVzc2FnZSlcbiAgICAgIGNvbmZpZ1NlcnZpY2Uuc2V0Q29uZmlnKHsgYWN0aXZlOiBmYWxzZSB9KVxuICAgIH1cbiAgfVxuXG4gIHNldFVzZXJDb250ZXh0KHVzZXJDb250ZXh0KSB7XG4gICAgdmFyIGNvbmZpZ1NlcnZpY2UgPSB0aGlzLnNlcnZpY2VGYWN0b3J5LmdldFNlcnZpY2UoQ09ORklHX1NFUlZJQ0UpXG4gICAgY29uZmlnU2VydmljZS5zZXRVc2VyQ29udGV4dCh1c2VyQ29udGV4dClcbiAgfVxuXG4gIHNldEN1c3RvbUNvbnRleHQoY3VzdG9tQ29udGV4dCkge1xuICAgIHZhciBjb25maWdTZXJ2aWNlID0gdGhpcy5zZXJ2aWNlRmFjdG9yeS5nZXRTZXJ2aWNlKENPTkZJR19TRVJWSUNFKVxuICAgIGNvbmZpZ1NlcnZpY2Uuc2V0Q3VzdG9tQ29udGV4dChjdXN0b21Db250ZXh0KVxuICB9XG5cbiAgYWRkTGFiZWxzKGxhYmVscykge1xuICAgIHZhciBjb25maWdTZXJ2aWNlID0gdGhpcy5zZXJ2aWNlRmFjdG9yeS5nZXRTZXJ2aWNlKENPTkZJR19TRVJWSUNFKVxuICAgIGNvbmZpZ1NlcnZpY2UuYWRkTGFiZWxzKGxhYmVscylcbiAgfVxuXG4gIC8vIFNob3VsZCBjYWxsIHRoaXMgbWV0aG9kIGJlZm9yZSAnbG9hZCcgZXZlbnQgb24gd2luZG93IGlzIGZpcmVkXG4gIHNldEluaXRpYWxQYWdlTG9hZE5hbWUobmFtZSkge1xuICAgIGNvbnN0IGNvbmZpZ1NlcnZpY2UgPSB0aGlzLnNlcnZpY2VGYWN0b3J5LmdldFNlcnZpY2UoQ09ORklHX1NFUlZJQ0UpXG4gICAgY29uZmlnU2VydmljZS5zZXRDb25maWcoe1xuICAgICAgcGFnZUxvYWRUcmFuc2FjdGlvbk5hbWU6IG5hbWVcbiAgICB9KVxuICB9XG5cbiAgc3RhcnRUcmFuc2FjdGlvbihuYW1lLCB0eXBlLCBvcHRpb25zKSB7XG4gICAgaWYgKHRoaXMuaXNFbmFibGVkKCkpIHtcbiAgICAgIHZhciB0cmFuc2FjdGlvblNlcnZpY2UgPSB0aGlzLnNlcnZpY2VGYWN0b3J5LmdldFNlcnZpY2UoXG4gICAgICAgIFRSQU5TQUNUSU9OX1NFUlZJQ0VcbiAgICAgIClcbiAgICAgIHJldHVybiB0cmFuc2FjdGlvblNlcnZpY2Uuc3RhcnRUcmFuc2FjdGlvbihuYW1lLCB0eXBlLCBvcHRpb25zKVxuICAgIH1cbiAgfVxuXG4gIHN0YXJ0U3BhbihuYW1lLCB0eXBlLCBvcHRpb25zKSB7XG4gICAgaWYgKHRoaXMuaXNFbmFibGVkKCkpIHtcbiAgICAgIHZhciB0cmFuc2FjdGlvblNlcnZpY2UgPSB0aGlzLnNlcnZpY2VGYWN0b3J5LmdldFNlcnZpY2UoXG4gICAgICAgIFRSQU5TQUNUSU9OX1NFUlZJQ0VcbiAgICAgIClcbiAgICAgIHJldHVybiB0cmFuc2FjdGlvblNlcnZpY2Uuc3RhcnRTcGFuKG5hbWUsIHR5cGUsIG9wdGlvbnMpXG4gICAgfVxuICB9XG5cbiAgZ2V0Q3VycmVudFRyYW5zYWN0aW9uKCkge1xuICAgIGlmICh0aGlzLmlzRW5hYmxlZCgpKSB7XG4gICAgICB2YXIgdHJhbnNhY3Rpb25TZXJ2aWNlID0gdGhpcy5zZXJ2aWNlRmFjdG9yeS5nZXRTZXJ2aWNlKFxuICAgICAgICBUUkFOU0FDVElPTl9TRVJWSUNFXG4gICAgICApXG4gICAgICByZXR1cm4gdHJhbnNhY3Rpb25TZXJ2aWNlLmdldEN1cnJlbnRUcmFuc2FjdGlvbigpXG4gICAgfVxuICB9XG5cbiAgY2FwdHVyZUVycm9yKGVycm9yKSB7XG4gICAgaWYgKHRoaXMuaXNFbmFibGVkKCkpIHtcbiAgICAgIHZhciBlcnJvckxvZ2dpbmcgPSB0aGlzLnNlcnZpY2VGYWN0b3J5LmdldFNlcnZpY2UoRVJST1JfTE9HR0lORylcbiAgICAgIHJldHVybiBlcnJvckxvZ2dpbmcubG9nRXJyb3IoZXJyb3IpXG4gICAgfVxuICB9XG5cbiAgYWRkRmlsdGVyKGZuKSB7XG4gICAgdmFyIGNvbmZpZ1NlcnZpY2UgPSB0aGlzLnNlcnZpY2VGYWN0b3J5LmdldFNlcnZpY2UoQ09ORklHX1NFUlZJQ0UpXG4gICAgY29uZmlnU2VydmljZS5hZGRGaWx0ZXIoZm4pXG4gIH1cbn1cbiIsIihmdW5jdGlvbihyb290LCBmYWN0b3J5KSB7XG4gICAgJ3VzZSBzdHJpY3QnO1xuICAgIC8vIFVuaXZlcnNhbCBNb2R1bGUgRGVmaW5pdGlvbiAoVU1EKSB0byBzdXBwb3J0IEFNRCwgQ29tbW9uSlMvTm9kZS5qcywgUmhpbm8sIGFuZCBicm93c2Vycy5cblxuICAgIC8qIGlzdGFuYnVsIGlnbm9yZSBuZXh0ICovXG4gICAgaWYgKHR5cGVvZiBkZWZpbmUgPT09ICdmdW5jdGlvbicgJiYgZGVmaW5lLmFtZCkge1xuICAgICAgICBkZWZpbmUoJ2Vycm9yLXN0YWNrLXBhcnNlcicsIFsnc3RhY2tmcmFtZSddLCBmYWN0b3J5KTtcbiAgICB9IGVsc2UgaWYgKHR5cGVvZiBleHBvcnRzID09PSAnb2JqZWN0Jykge1xuICAgICAgICBtb2R1bGUuZXhwb3J0cyA9IGZhY3RvcnkocmVxdWlyZSgnc3RhY2tmcmFtZScpKTtcbiAgICB9IGVsc2Uge1xuICAgICAgICByb290LkVycm9yU3RhY2tQYXJzZXIgPSBmYWN0b3J5KHJvb3QuU3RhY2tGcmFtZSk7XG4gICAgfVxufSh0aGlzLCBmdW5jdGlvbiBFcnJvclN0YWNrUGFyc2VyKFN0YWNrRnJhbWUpIHtcbiAgICAndXNlIHN0cmljdCc7XG5cbiAgICB2YXIgRklSRUZPWF9TQUZBUklfU1RBQ0tfUkVHRVhQID0gLyhefEApXFxTK1xcOlxcZCsvO1xuICAgIHZhciBDSFJPTUVfSUVfU1RBQ0tfUkVHRVhQID0gL15cXHMqYXQgLiooXFxTK1xcOlxcZCt8XFwobmF0aXZlXFwpKS9tO1xuICAgIHZhciBTQUZBUklfTkFUSVZFX0NPREVfUkVHRVhQID0gL14oZXZhbEApPyhcXFtuYXRpdmUgY29kZVxcXSk/JC87XG5cbiAgICBmdW5jdGlvbiBfbWFwKGFycmF5LCBmbiwgdGhpc0FyZykge1xuICAgICAgICBpZiAodHlwZW9mIEFycmF5LnByb3RvdHlwZS5tYXAgPT09ICdmdW5jdGlvbicpIHtcbiAgICAgICAgICAgIHJldHVybiBhcnJheS5tYXAoZm4sIHRoaXNBcmcpO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgdmFyIG91dHB1dCA9IG5ldyBBcnJheShhcnJheS5sZW5ndGgpO1xuICAgICAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCBhcnJheS5sZW5ndGg7IGkrKykge1xuICAgICAgICAgICAgICAgIG91dHB1dFtpXSA9IGZuLmNhbGwodGhpc0FyZywgYXJyYXlbaV0pO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgcmV0dXJuIG91dHB1dDtcbiAgICAgICAgfVxuICAgIH1cblxuICAgIGZ1bmN0aW9uIF9maWx0ZXIoYXJyYXksIGZuLCB0aGlzQXJnKSB7XG4gICAgICAgIGlmICh0eXBlb2YgQXJyYXkucHJvdG90eXBlLmZpbHRlciA9PT0gJ2Z1bmN0aW9uJykge1xuICAgICAgICAgICAgcmV0dXJuIGFycmF5LmZpbHRlcihmbiwgdGhpc0FyZyk7XG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgICB2YXIgb3V0cHV0ID0gW107XG4gICAgICAgICAgICBmb3IgKHZhciBpID0gMDsgaSA8IGFycmF5Lmxlbmd0aDsgaSsrKSB7XG4gICAgICAgICAgICAgICAgaWYgKGZuLmNhbGwodGhpc0FyZywgYXJyYXlbaV0pKSB7XG4gICAgICAgICAgICAgICAgICAgIG91dHB1dC5wdXNoKGFycmF5W2ldKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICByZXR1cm4gb3V0cHV0O1xuICAgICAgICB9XG4gICAgfVxuXG4gICAgZnVuY3Rpb24gX2luZGV4T2YoYXJyYXksIHRhcmdldCkge1xuICAgICAgICBpZiAodHlwZW9mIEFycmF5LnByb3RvdHlwZS5pbmRleE9mID09PSAnZnVuY3Rpb24nKSB7XG4gICAgICAgICAgICByZXR1cm4gYXJyYXkuaW5kZXhPZih0YXJnZXQpO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgZm9yICh2YXIgaSA9IDA7IGkgPCBhcnJheS5sZW5ndGg7IGkrKykge1xuICAgICAgICAgICAgICAgIGlmIChhcnJheVtpXSA9PT0gdGFyZ2V0KSB7XG4gICAgICAgICAgICAgICAgICAgIHJldHVybiBpO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIHJldHVybiAtMTtcbiAgICAgICAgfVxuICAgIH1cblxuICAgIHJldHVybiB7XG4gICAgICAgIC8qKlxuICAgICAgICAgKiBHaXZlbiBhbiBFcnJvciBvYmplY3QsIGV4dHJhY3QgdGhlIG1vc3QgaW5mb3JtYXRpb24gZnJvbSBpdC5cbiAgICAgICAgICpcbiAgICAgICAgICogQHBhcmFtIHtFcnJvcn0gZXJyb3Igb2JqZWN0XG4gICAgICAgICAqIEByZXR1cm4ge0FycmF5fSBvZiBTdGFja0ZyYW1lc1xuICAgICAgICAgKi9cbiAgICAgICAgcGFyc2U6IGZ1bmN0aW9uIEVycm9yU3RhY2tQYXJzZXIkJHBhcnNlKGVycm9yKSB7XG4gICAgICAgICAgICBpZiAodHlwZW9mIGVycm9yLnN0YWNrdHJhY2UgIT09ICd1bmRlZmluZWQnIHx8IHR5cGVvZiBlcnJvclsnb3BlcmEjc291cmNlbG9jJ10gIT09ICd1bmRlZmluZWQnKSB7XG4gICAgICAgICAgICAgICAgcmV0dXJuIHRoaXMucGFyc2VPcGVyYShlcnJvcik7XG4gICAgICAgICAgICB9IGVsc2UgaWYgKGVycm9yLnN0YWNrICYmIGVycm9yLnN0YWNrLm1hdGNoKENIUk9NRV9JRV9TVEFDS19SRUdFWFApKSB7XG4gICAgICAgICAgICAgICAgcmV0dXJuIHRoaXMucGFyc2VWOE9ySUUoZXJyb3IpO1xuICAgICAgICAgICAgfSBlbHNlIGlmIChlcnJvci5zdGFjaykge1xuICAgICAgICAgICAgICAgIHJldHVybiB0aGlzLnBhcnNlRkZPclNhZmFyaShlcnJvcik7XG4gICAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgICAgIHRocm93IG5ldyBFcnJvcignQ2Fubm90IHBhcnNlIGdpdmVuIEVycm9yIG9iamVjdCcpO1xuICAgICAgICAgICAgfVxuICAgICAgICB9LFxuXG4gICAgICAgIC8vIFNlcGFyYXRlIGxpbmUgYW5kIGNvbHVtbiBudW1iZXJzIGZyb20gYSBzdHJpbmcgb2YgdGhlIGZvcm06IChVUkk6TGluZTpDb2x1bW4pXG4gICAgICAgIGV4dHJhY3RMb2NhdGlvbjogZnVuY3Rpb24gRXJyb3JTdGFja1BhcnNlciQkZXh0cmFjdExvY2F0aW9uKHVybExpa2UpIHtcbiAgICAgICAgICAgIC8vIEZhaWwtZmFzdCBidXQgcmV0dXJuIGxvY2F0aW9ucyBsaWtlIFwiKG5hdGl2ZSlcIlxuICAgICAgICAgICAgaWYgKHVybExpa2UuaW5kZXhPZignOicpID09PSAtMSkge1xuICAgICAgICAgICAgICAgIHJldHVybiBbdXJsTGlrZV07XG4gICAgICAgICAgICB9XG5cbiAgICAgICAgICAgIHZhciByZWdFeHAgPSAvKC4rPykoPzpcXDooXFxkKykpPyg/OlxcOihcXGQrKSk/JC87XG4gICAgICAgICAgICB2YXIgcGFydHMgPSByZWdFeHAuZXhlYyh1cmxMaWtlLnJlcGxhY2UoL1tcXChcXCldL2csICcnKSk7XG4gICAgICAgICAgICByZXR1cm4gW3BhcnRzWzFdLCBwYXJ0c1syXSB8fCB1bmRlZmluZWQsIHBhcnRzWzNdIHx8IHVuZGVmaW5lZF07XG4gICAgICAgIH0sXG5cbiAgICAgICAgcGFyc2VWOE9ySUU6IGZ1bmN0aW9uIEVycm9yU3RhY2tQYXJzZXIkJHBhcnNlVjhPcklFKGVycm9yKSB7XG4gICAgICAgICAgICB2YXIgZmlsdGVyZWQgPSBfZmlsdGVyKGVycm9yLnN0YWNrLnNwbGl0KCdcXG4nKSwgZnVuY3Rpb24obGluZSkge1xuICAgICAgICAgICAgICAgIHJldHVybiAhIWxpbmUubWF0Y2goQ0hST01FX0lFX1NUQUNLX1JFR0VYUCk7XG4gICAgICAgICAgICB9LCB0aGlzKTtcblxuICAgICAgICAgICAgcmV0dXJuIF9tYXAoZmlsdGVyZWQsIGZ1bmN0aW9uKGxpbmUpIHtcbiAgICAgICAgICAgICAgICBpZiAobGluZS5pbmRleE9mKCcoZXZhbCAnKSA+IC0xKSB7XG4gICAgICAgICAgICAgICAgICAgIC8vIFRocm93IGF3YXkgZXZhbCBpbmZvcm1hdGlvbiB1bnRpbCB3ZSBpbXBsZW1lbnQgc3RhY2t0cmFjZS5qcy9zdGFja2ZyYW1lIzhcbiAgICAgICAgICAgICAgICAgICAgbGluZSA9IGxpbmUucmVwbGFjZSgvZXZhbCBjb2RlL2csICdldmFsJykucmVwbGFjZSgvKFxcKGV2YWwgYXQgW15cXCgpXSopfChcXClcXCwuKiQpL2csICcnKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICAgICAgdmFyIHRva2VucyA9IGxpbmUucmVwbGFjZSgvXlxccysvLCAnJykucmVwbGFjZSgvXFwoZXZhbCBjb2RlL2csICcoJykuc3BsaXQoL1xccysvKS5zbGljZSgxKTtcbiAgICAgICAgICAgICAgICB2YXIgbG9jYXRpb25QYXJ0cyA9IHRoaXMuZXh0cmFjdExvY2F0aW9uKHRva2Vucy5wb3AoKSk7XG4gICAgICAgICAgICAgICAgdmFyIGZ1bmN0aW9uTmFtZSA9IHRva2Vucy5qb2luKCcgJykgfHwgdW5kZWZpbmVkO1xuICAgICAgICAgICAgICAgIHZhciBmaWxlTmFtZSA9IF9pbmRleE9mKFsnZXZhbCcsICc8YW5vbnltb3VzPiddLCBsb2NhdGlvblBhcnRzWzBdKSA+IC0xID8gdW5kZWZpbmVkIDogbG9jYXRpb25QYXJ0c1swXTtcblxuICAgICAgICAgICAgICAgIHJldHVybiBuZXcgU3RhY2tGcmFtZShmdW5jdGlvbk5hbWUsIHVuZGVmaW5lZCwgZmlsZU5hbWUsIGxvY2F0aW9uUGFydHNbMV0sIGxvY2F0aW9uUGFydHNbMl0sIGxpbmUpO1xuICAgICAgICAgICAgfSwgdGhpcyk7XG4gICAgICAgIH0sXG5cbiAgICAgICAgcGFyc2VGRk9yU2FmYXJpOiBmdW5jdGlvbiBFcnJvclN0YWNrUGFyc2VyJCRwYXJzZUZGT3JTYWZhcmkoZXJyb3IpIHtcbiAgICAgICAgICAgIHZhciBmaWx0ZXJlZCA9IF9maWx0ZXIoZXJyb3Iuc3RhY2suc3BsaXQoJ1xcbicpLCBmdW5jdGlvbihsaW5lKSB7XG4gICAgICAgICAgICAgICAgcmV0dXJuICFsaW5lLm1hdGNoKFNBRkFSSV9OQVRJVkVfQ09ERV9SRUdFWFApO1xuICAgICAgICAgICAgfSwgdGhpcyk7XG5cbiAgICAgICAgICAgIHJldHVybiBfbWFwKGZpbHRlcmVkLCBmdW5jdGlvbihsaW5lKSB7XG4gICAgICAgICAgICAgICAgLy8gVGhyb3cgYXdheSBldmFsIGluZm9ybWF0aW9uIHVudGlsIHdlIGltcGxlbWVudCBzdGFja3RyYWNlLmpzL3N0YWNrZnJhbWUjOFxuICAgICAgICAgICAgICAgIGlmIChsaW5lLmluZGV4T2YoJyA+IGV2YWwnKSA+IC0xKSB7XG4gICAgICAgICAgICAgICAgICAgIGxpbmUgPSBsaW5lLnJlcGxhY2UoLyBsaW5lIChcXGQrKSg/OiA+IGV2YWwgbGluZSBcXGQrKSogPiBldmFsXFw6XFxkK1xcOlxcZCsvZywgJzokMScpO1xuICAgICAgICAgICAgICAgIH1cblxuICAgICAgICAgICAgICAgIGlmIChsaW5lLmluZGV4T2YoJ0AnKSA9PT0gLTEgJiYgbGluZS5pbmRleE9mKCc6JykgPT09IC0xKSB7XG4gICAgICAgICAgICAgICAgICAgIC8vIFNhZmFyaSBldmFsIGZyYW1lcyBvbmx5IGhhdmUgZnVuY3Rpb24gbmFtZXMgYW5kIG5vdGhpbmcgZWxzZVxuICAgICAgICAgICAgICAgICAgICByZXR1cm4gbmV3IFN0YWNrRnJhbWUobGluZSk7XG4gICAgICAgICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgICAgICAgICAgdmFyIHRva2VucyA9IGxpbmUuc3BsaXQoJ0AnKTtcbiAgICAgICAgICAgICAgICAgICAgdmFyIGxvY2F0aW9uUGFydHMgPSB0aGlzLmV4dHJhY3RMb2NhdGlvbih0b2tlbnMucG9wKCkpO1xuICAgICAgICAgICAgICAgICAgICB2YXIgZnVuY3Rpb25OYW1lID0gdG9rZW5zLmpvaW4oJ0AnKSB8fCB1bmRlZmluZWQ7XG4gICAgICAgICAgICAgICAgICAgIHJldHVybiBuZXcgU3RhY2tGcmFtZShmdW5jdGlvbk5hbWUsXG4gICAgICAgICAgICAgICAgICAgICAgICB1bmRlZmluZWQsXG4gICAgICAgICAgICAgICAgICAgICAgICBsb2NhdGlvblBhcnRzWzBdLFxuICAgICAgICAgICAgICAgICAgICAgICAgbG9jYXRpb25QYXJ0c1sxXSxcbiAgICAgICAgICAgICAgICAgICAgICAgIGxvY2F0aW9uUGFydHNbMl0sXG4gICAgICAgICAgICAgICAgICAgICAgICBsaW5lKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9LCB0aGlzKTtcbiAgICAgICAgfSxcblxuICAgICAgICBwYXJzZU9wZXJhOiBmdW5jdGlvbiBFcnJvclN0YWNrUGFyc2VyJCRwYXJzZU9wZXJhKGUpIHtcbiAgICAgICAgICAgIGlmICghZS5zdGFja3RyYWNlIHx8IChlLm1lc3NhZ2UuaW5kZXhPZignXFxuJykgPiAtMSAmJlxuICAgICAgICAgICAgICAgIGUubWVzc2FnZS5zcGxpdCgnXFxuJykubGVuZ3RoID4gZS5zdGFja3RyYWNlLnNwbGl0KCdcXG4nKS5sZW5ndGgpKSB7XG4gICAgICAgICAgICAgICAgcmV0dXJuIHRoaXMucGFyc2VPcGVyYTkoZSk7XG4gICAgICAgICAgICB9IGVsc2UgaWYgKCFlLnN0YWNrKSB7XG4gICAgICAgICAgICAgICAgcmV0dXJuIHRoaXMucGFyc2VPcGVyYTEwKGUpO1xuICAgICAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICAgICAgICByZXR1cm4gdGhpcy5wYXJzZU9wZXJhMTEoZSk7XG4gICAgICAgICAgICB9XG4gICAgICAgIH0sXG5cbiAgICAgICAgcGFyc2VPcGVyYTk6IGZ1bmN0aW9uIEVycm9yU3RhY2tQYXJzZXIkJHBhcnNlT3BlcmE5KGUpIHtcbiAgICAgICAgICAgIHZhciBsaW5lUkUgPSAvTGluZSAoXFxkKykuKnNjcmlwdCAoPzppbiApPyhcXFMrKS9pO1xuICAgICAgICAgICAgdmFyIGxpbmVzID0gZS5tZXNzYWdlLnNwbGl0KCdcXG4nKTtcbiAgICAgICAgICAgIHZhciByZXN1bHQgPSBbXTtcblxuICAgICAgICAgICAgZm9yICh2YXIgaSA9IDIsIGxlbiA9IGxpbmVzLmxlbmd0aDsgaSA8IGxlbjsgaSArPSAyKSB7XG4gICAgICAgICAgICAgICAgdmFyIG1hdGNoID0gbGluZVJFLmV4ZWMobGluZXNbaV0pO1xuICAgICAgICAgICAgICAgIGlmIChtYXRjaCkge1xuICAgICAgICAgICAgICAgICAgICByZXN1bHQucHVzaChuZXcgU3RhY2tGcmFtZSh1bmRlZmluZWQsIHVuZGVmaW5lZCwgbWF0Y2hbMl0sIG1hdGNoWzFdLCB1bmRlZmluZWQsIGxpbmVzW2ldKSk7XG4gICAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgfVxuXG4gICAgICAgICAgICByZXR1cm4gcmVzdWx0O1xuICAgICAgICB9LFxuXG4gICAgICAgIHBhcnNlT3BlcmExMDogZnVuY3Rpb24gRXJyb3JTdGFja1BhcnNlciQkcGFyc2VPcGVyYTEwKGUpIHtcbiAgICAgICAgICAgIHZhciBsaW5lUkUgPSAvTGluZSAoXFxkKykuKnNjcmlwdCAoPzppbiApPyhcXFMrKSg/OjogSW4gZnVuY3Rpb24gKFxcUyspKT8kL2k7XG4gICAgICAgICAgICB2YXIgbGluZXMgPSBlLnN0YWNrdHJhY2Uuc3BsaXQoJ1xcbicpO1xuICAgICAgICAgICAgdmFyIHJlc3VsdCA9IFtdO1xuXG4gICAgICAgICAgICBmb3IgKHZhciBpID0gMCwgbGVuID0gbGluZXMubGVuZ3RoOyBpIDwgbGVuOyBpICs9IDIpIHtcbiAgICAgICAgICAgICAgICB2YXIgbWF0Y2ggPSBsaW5lUkUuZXhlYyhsaW5lc1tpXSk7XG4gICAgICAgICAgICAgICAgaWYgKG1hdGNoKSB7XG4gICAgICAgICAgICAgICAgICAgIHJlc3VsdC5wdXNoKFxuICAgICAgICAgICAgICAgICAgICAgICAgbmV3IFN0YWNrRnJhbWUoXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgbWF0Y2hbM10gfHwgdW5kZWZpbmVkLFxuICAgICAgICAgICAgICAgICAgICAgICAgICAgIHVuZGVmaW5lZCxcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBtYXRjaFsyXSxcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICBtYXRjaFsxXSxcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICB1bmRlZmluZWQsXG4gICAgICAgICAgICAgICAgICAgICAgICAgICAgbGluZXNbaV1cbiAgICAgICAgICAgICAgICAgICAgICAgIClcbiAgICAgICAgICAgICAgICAgICAgKTtcbiAgICAgICAgICAgICAgICB9XG4gICAgICAgICAgICB9XG5cbiAgICAgICAgICAgIHJldHVybiByZXN1bHQ7XG4gICAgICAgIH0sXG5cbiAgICAgICAgLy8gT3BlcmEgMTAuNjUrIEVycm9yLnN0YWNrIHZlcnkgc2ltaWxhciB0byBGRi9TYWZhcmlcbiAgICAgICAgcGFyc2VPcGVyYTExOiBmdW5jdGlvbiBFcnJvclN0YWNrUGFyc2VyJCRwYXJzZU9wZXJhMTEoZXJyb3IpIHtcbiAgICAgICAgICAgIHZhciBmaWx0ZXJlZCA9IF9maWx0ZXIoZXJyb3Iuc3RhY2suc3BsaXQoJ1xcbicpLCBmdW5jdGlvbihsaW5lKSB7XG4gICAgICAgICAgICAgICAgcmV0dXJuICEhbGluZS5tYXRjaChGSVJFRk9YX1NBRkFSSV9TVEFDS19SRUdFWFApICYmICFsaW5lLm1hdGNoKC9eRXJyb3IgY3JlYXRlZCBhdC8pO1xuICAgICAgICAgICAgfSwgdGhpcyk7XG5cbiAgICAgICAgICAgIHJldHVybiBfbWFwKGZpbHRlcmVkLCBmdW5jdGlvbihsaW5lKSB7XG4gICAgICAgICAgICAgICAgdmFyIHRva2VucyA9IGxpbmUuc3BsaXQoJ0AnKTtcbiAgICAgICAgICAgICAgICB2YXIgbG9jYXRpb25QYXJ0cyA9IHRoaXMuZXh0cmFjdExvY2F0aW9uKHRva2Vucy5wb3AoKSk7XG4gICAgICAgICAgICAgICAgdmFyIGZ1bmN0aW9uQ2FsbCA9ICh0b2tlbnMuc2hpZnQoKSB8fCAnJyk7XG4gICAgICAgICAgICAgICAgdmFyIGZ1bmN0aW9uTmFtZSA9IGZ1bmN0aW9uQ2FsbFxuICAgICAgICAgICAgICAgICAgICAgICAgLnJlcGxhY2UoLzxhbm9ueW1vdXMgZnVuY3Rpb24oOiAoXFx3KykpPz4vLCAnJDInKVxuICAgICAgICAgICAgICAgICAgICAgICAgLnJlcGxhY2UoL1xcKFteXFwpXSpcXCkvZywgJycpIHx8IHVuZGVmaW5lZDtcbiAgICAgICAgICAgICAgICB2YXIgYXJnc1JhdztcbiAgICAgICAgICAgICAgICBpZiAoZnVuY3Rpb25DYWxsLm1hdGNoKC9cXCgoW15cXCldKilcXCkvKSkge1xuICAgICAgICAgICAgICAgICAgICBhcmdzUmF3ID0gZnVuY3Rpb25DYWxsLnJlcGxhY2UoL15bXlxcKF0rXFwoKFteXFwpXSopXFwpJC8sICckMScpO1xuICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICB2YXIgYXJncyA9IChhcmdzUmF3ID09PSB1bmRlZmluZWQgfHwgYXJnc1JhdyA9PT0gJ1thcmd1bWVudHMgbm90IGF2YWlsYWJsZV0nKSA/XG4gICAgICAgICAgICAgICAgICAgIHVuZGVmaW5lZCA6IGFyZ3NSYXcuc3BsaXQoJywnKTtcbiAgICAgICAgICAgICAgICByZXR1cm4gbmV3IFN0YWNrRnJhbWUoXG4gICAgICAgICAgICAgICAgICAgIGZ1bmN0aW9uTmFtZSxcbiAgICAgICAgICAgICAgICAgICAgYXJncyxcbiAgICAgICAgICAgICAgICAgICAgbG9jYXRpb25QYXJ0c1swXSxcbiAgICAgICAgICAgICAgICAgICAgbG9jYXRpb25QYXJ0c1sxXSxcbiAgICAgICAgICAgICAgICAgICAgbG9jYXRpb25QYXJ0c1syXSxcbiAgICAgICAgICAgICAgICAgICAgbGluZSk7XG4gICAgICAgICAgICB9LCB0aGlzKTtcbiAgICAgICAgfVxuICAgIH07XG59KSk7XG5cbiIsIlwidXNlIHN0cmljdFwiO1xuT2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIFwiX19lc01vZHVsZVwiLCB7IHZhbHVlOiB0cnVlIH0pO1xuLyoqXG4gKiBUaGUgRk9STUFUX0JJTkFSWSBmb3JtYXQgcmVwcmVzZW50cyBTcGFuQ29udGV4dHMgaW4gYW4gb3BhcXVlIGJpbmFyeVxuICogY2Fycmllci5cbiAqXG4gKiBUcmFjZXIuaW5qZWN0KCkgd2lsbCBzZXQgdGhlIGJ1ZmZlciBmaWVsZCB0byBhbiBBcnJheS1saWtlIChBcnJheSxcbiAqIEFycmF5QnVmZmVyLCBvciBUeXBlZEJ1ZmZlcikgb2JqZWN0IGNvbnRhaW5pbmcgdGhlIGluamVjdGVkIGJpbmFyeSBkYXRhLlxuICogQW55IHZhbGlkIE9iamVjdCBjYW4gYmUgdXNlZCBhcyBsb25nIGFzIHRoZSBidWZmZXIgZmllbGQgb2YgdGhlIG9iamVjdFxuICogY2FuIGJlIHNldC5cbiAqXG4gKiBUcmFjZXIuZXh0cmFjdCgpIHdpbGwgbG9vayBmb3IgYGNhcnJpZXIuYnVmZmVyYCwgYW5kIHRoYXQgZmllbGQgaXNcbiAqIGV4cGVjdGVkIHRvIGJlIGFuIEFycmF5LWxpa2Ugb2JqZWN0IChBcnJheSwgQXJyYXlCdWZmZXIsIG9yXG4gKiBUeXBlZEJ1ZmZlcikuXG4gKi9cbmV4cG9ydHMuRk9STUFUX0JJTkFSWSA9ICdiaW5hcnknO1xuLyoqXG4gKiBUaGUgRk9STUFUX1RFWFRfTUFQIGZvcm1hdCByZXByZXNlbnRzIFNwYW5Db250ZXh0cyB1c2luZyBhXG4gKiBzdHJpbmctPnN0cmluZyBtYXAgKGJhY2tlZCBieSBhIEphdmFzY3JpcHQgT2JqZWN0KSBhcyBhIGNhcnJpZXIuXG4gKlxuICogTk9URTogVW5saWtlIEZPUk1BVF9IVFRQX0hFQURFUlMsIEZPUk1BVF9URVhUX01BUCBwbGFjZXMgbm8gcmVzdHJpY3Rpb25zXG4gKiBvbiB0aGUgY2hhcmFjdGVycyB1c2VkIGluIGVpdGhlciB0aGUga2V5cyBvciB0aGUgdmFsdWVzIG9mIHRoZSBtYXBcbiAqIGVudHJpZXMuXG4gKlxuICogVGhlIEZPUk1BVF9URVhUX01BUCBjYXJyaWVyIG1hcCBtYXkgY29udGFpbiB1bnJlbGF0ZWQgZGF0YSAoZS5nLixcbiAqIGFyYml0cmFyeSBnUlBDIG1ldGFkYXRhKTsgYXMgc3VjaCwgdGhlIFRyYWNlciBpbXBsZW1lbnRhdGlvbiBzaG91bGQgdXNlXG4gKiBhIHByZWZpeCBvciBvdGhlciBjb252ZW50aW9uIHRvIGRpc3Rpbmd1aXNoIFRyYWNlci1zcGVjaWZpYyBrZXk6dmFsdWVcbiAqIHBhaXJzLlxuICovXG5leHBvcnRzLkZPUk1BVF9URVhUX01BUCA9ICd0ZXh0X21hcCc7XG4vKipcbiAqIFRoZSBGT1JNQVRfSFRUUF9IRUFERVJTIGZvcm1hdCByZXByZXNlbnRzIFNwYW5Db250ZXh0cyB1c2luZyBhXG4gKiBjaGFyYWN0ZXItcmVzdHJpY3RlZCBzdHJpbmctPnN0cmluZyBtYXAgKGJhY2tlZCBieSBhIEphdmFzY3JpcHQgT2JqZWN0KVxuICogYXMgYSBjYXJyaWVyLlxuICpcbiAqIEtleXMgYW5kIHZhbHVlcyBpbiB0aGUgRk9STUFUX0hUVFBfSEVBREVSUyBjYXJyaWVyIG11c3QgYmUgc3VpdGFibGUgZm9yXG4gKiB1c2UgYXMgSFRUUCBoZWFkZXJzICh3aXRob3V0IG1vZGlmaWNhdGlvbiBvciBmdXJ0aGVyIGVzY2FwaW5nKS4gVGhhdCBpcyxcbiAqIHRoZSBrZXlzIGhhdmUgYSBncmVhdGx5IHJlc3RyaWN0ZWQgY2hhcmFjdGVyIHNldCwgY2FzaW5nIGZvciB0aGUga2V5c1xuICogbWF5IG5vdCBiZSBwcmVzZXJ2ZWQgYnkgdmFyaW91cyBpbnRlcm1lZGlhcmllcywgYW5kIHRoZSB2YWx1ZXMgc2hvdWxkIGJlXG4gKiBVUkwtZXNjYXBlZC5cbiAqXG4gKiBUaGUgRk9STUFUX0hUVFBfSEVBREVSUyBjYXJyaWVyIG1hcCBtYXkgY29udGFpbiB1bnJlbGF0ZWQgZGF0YSAoZS5nLixcbiAqIGFyYml0cmFyeSBIVFRQIGhlYWRlcnMpOyBhcyBzdWNoLCB0aGUgVHJhY2VyIGltcGxlbWVudGF0aW9uIHNob3VsZCB1c2UgYVxuICogcHJlZml4IG9yIG90aGVyIGNvbnZlbnRpb24gdG8gZGlzdGluZ3Vpc2ggVHJhY2VyLXNwZWNpZmljIGtleTp2YWx1ZVxuICogcGFpcnMuXG4gKi9cbmV4cG9ydHMuRk9STUFUX0hUVFBfSEVBREVSUyA9ICdodHRwX2hlYWRlcnMnO1xuLyoqXG4gKiBBIFNwYW4gbWF5IGJlIHRoZSBcImNoaWxkIG9mXCIgYSBwYXJlbnQgU3Bhbi4gSW4gYSDigJxjaGlsZCBvZuKAnSByZWZlcmVuY2UsXG4gKiB0aGUgcGFyZW50IFNwYW4gZGVwZW5kcyBvbiB0aGUgY2hpbGQgU3BhbiBpbiBzb21lIGNhcGFjaXR5LlxuICpcbiAqIFNlZSBtb3JlIGFib3V0IHJlZmVyZW5jZSB0eXBlcyBhdCBodHRwczovL2dpdGh1Yi5jb20vb3BlbnRyYWNpbmcvc3BlY2lmaWNhdGlvblxuICovXG5leHBvcnRzLlJFRkVSRU5DRV9DSElMRF9PRiA9ICdjaGlsZF9vZic7XG4vKipcbiAqIFNvbWUgcGFyZW50IFNwYW5zIGRvIG5vdCBkZXBlbmQgaW4gYW55IHdheSBvbiB0aGUgcmVzdWx0IG9mIHRoZWlyIGNoaWxkXG4gKiBTcGFucy4gSW4gdGhlc2UgY2FzZXMsIHdlIHNheSBtZXJlbHkgdGhhdCB0aGUgY2hpbGQgU3BhbiDigJxmb2xsb3dzIGZyb23igJ1cbiAqIHRoZSBwYXJlbnQgU3BhbiBpbiBhIGNhdXNhbCBzZW5zZS5cbiAqXG4gKiBTZWUgbW9yZSBhYm91dCByZWZlcmVuY2UgdHlwZXMgYXQgaHR0cHM6Ly9naXRodWIuY29tL29wZW50cmFjaW5nL3NwZWNpZmljYXRpb25cbiAqL1xuZXhwb3J0cy5SRUZFUkVOQ0VfRk9MTE9XU19GUk9NID0gJ2ZvbGxvd3NfZnJvbSc7XG4vLyMgc291cmNlTWFwcGluZ1VSTD1jb25zdGFudHMuanMubWFwIiwiXCJ1c2Ugc3RyaWN0XCI7XG5PYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgXCJfX2VzTW9kdWxlXCIsIHsgdmFsdWU6IHRydWUgfSk7XG52YXIgQ29uc3RhbnRzID0gcmVxdWlyZShcIi4vY29uc3RhbnRzXCIpO1xudmFyIHJlZmVyZW5jZV8xID0gcmVxdWlyZShcIi4vcmVmZXJlbmNlXCIpO1xudmFyIHNwYW5fMSA9IHJlcXVpcmUoXCIuL3NwYW5cIik7XG4vKipcbiAqIFJldHVybiBhIG5ldyBSRUZFUkVOQ0VfQ0hJTERfT0YgcmVmZXJlbmNlLlxuICpcbiAqIEBwYXJhbSB7U3BhbkNvbnRleHR9IHNwYW5Db250ZXh0IC0gdGhlIHBhcmVudCBTcGFuQ29udGV4dCBpbnN0YW5jZSB0b1xuICogICAgICAgIHJlZmVyZW5jZS5cbiAqIEByZXR1cm4gYSBSRUZFUkVOQ0VfQ0hJTERfT0YgcmVmZXJlbmNlIHBvaW50aW5nIHRvIGBzcGFuQ29udGV4dGBcbiAqL1xuZnVuY3Rpb24gY2hpbGRPZihzcGFuQ29udGV4dCkge1xuICAgIC8vIEFsbG93IHRoZSB1c2VyIHRvIHBhc3MgYSBTcGFuIGluc3RlYWQgb2YgYSBTcGFuQ29udGV4dFxuICAgIGlmIChzcGFuQ29udGV4dCBpbnN0YW5jZW9mIHNwYW5fMS5kZWZhdWx0KSB7XG4gICAgICAgIHNwYW5Db250ZXh0ID0gc3BhbkNvbnRleHQuY29udGV4dCgpO1xuICAgIH1cbiAgICByZXR1cm4gbmV3IHJlZmVyZW5jZV8xLmRlZmF1bHQoQ29uc3RhbnRzLlJFRkVSRU5DRV9DSElMRF9PRiwgc3BhbkNvbnRleHQpO1xufVxuZXhwb3J0cy5jaGlsZE9mID0gY2hpbGRPZjtcbi8qKlxuICogUmV0dXJuIGEgbmV3IFJFRkVSRU5DRV9GT0xMT1dTX0ZST00gcmVmZXJlbmNlLlxuICpcbiAqIEBwYXJhbSB7U3BhbkNvbnRleHR9IHNwYW5Db250ZXh0IC0gdGhlIHBhcmVudCBTcGFuQ29udGV4dCBpbnN0YW5jZSB0b1xuICogICAgICAgIHJlZmVyZW5jZS5cbiAqIEByZXR1cm4gYSBSRUZFUkVOQ0VfRk9MTE9XU19GUk9NIHJlZmVyZW5jZSBwb2ludGluZyB0byBgc3BhbkNvbnRleHRgXG4gKi9cbmZ1bmN0aW9uIGZvbGxvd3NGcm9tKHNwYW5Db250ZXh0KSB7XG4gICAgLy8gQWxsb3cgdGhlIHVzZXIgdG8gcGFzcyBhIFNwYW4gaW5zdGVhZCBvZiBhIFNwYW5Db250ZXh0XG4gICAgaWYgKHNwYW5Db250ZXh0IGluc3RhbmNlb2Ygc3Bhbl8xLmRlZmF1bHQpIHtcbiAgICAgICAgc3BhbkNvbnRleHQgPSBzcGFuQ29udGV4dC5jb250ZXh0KCk7XG4gICAgfVxuICAgIHJldHVybiBuZXcgcmVmZXJlbmNlXzEuZGVmYXVsdChDb25zdGFudHMuUkVGRVJFTkNFX0ZPTExPV1NfRlJPTSwgc3BhbkNvbnRleHQpO1xufVxuZXhwb3J0cy5mb2xsb3dzRnJvbSA9IGZvbGxvd3NGcm9tO1xuLy8jIHNvdXJjZU1hcHBpbmdVUkw9ZnVuY3Rpb25zLmpzLm1hcCIsIlwidXNlIHN0cmljdFwiO1xuT2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIFwiX19lc01vZHVsZVwiLCB7IHZhbHVlOiB0cnVlIH0pO1xudmFyIHNwYW5fMSA9IHJlcXVpcmUoXCIuL3NwYW5cIik7XG52YXIgc3Bhbl9jb250ZXh0XzEgPSByZXF1aXJlKFwiLi9zcGFuX2NvbnRleHRcIik7XG52YXIgdHJhY2VyXzEgPSByZXF1aXJlKFwiLi90cmFjZXJcIik7XG5leHBvcnRzLnRyYWNlciA9IG51bGw7XG5leHBvcnRzLnNwYW5Db250ZXh0ID0gbnVsbDtcbmV4cG9ydHMuc3BhbiA9IG51bGw7XG4vLyBEZWZlcnJlZCBpbml0aWFsaXphdGlvbiB0byBhdm9pZCBhIGRlcGVuZGVuY3kgY3ljbGUgd2hlcmUgVHJhY2VyIGRlcGVuZHMgb25cbi8vIFNwYW4gd2hpY2ggZGVwZW5kcyBvbiB0aGUgbm9vcCB0cmFjZXIuXG5mdW5jdGlvbiBpbml0aWFsaXplKCkge1xuICAgIGV4cG9ydHMudHJhY2VyID0gbmV3IHRyYWNlcl8xLmRlZmF1bHQoKTtcbiAgICBleHBvcnRzLnNwYW4gPSBuZXcgc3Bhbl8xLmRlZmF1bHQoKTtcbiAgICBleHBvcnRzLnNwYW5Db250ZXh0ID0gbmV3IHNwYW5fY29udGV4dF8xLmRlZmF1bHQoKTtcbn1cbmV4cG9ydHMuaW5pdGlhbGl6ZSA9IGluaXRpYWxpemU7XG4vLyMgc291cmNlTWFwcGluZ1VSTD1ub29wLmpzLm1hcCIsIlwidXNlIHN0cmljdFwiO1xuT2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIFwiX19lc01vZHVsZVwiLCB7IHZhbHVlOiB0cnVlIH0pO1xudmFyIHNwYW5fMSA9IHJlcXVpcmUoXCIuL3NwYW5cIik7XG4vKipcbiAqIFJlZmVyZW5jZSBwYWlycyBhIHJlZmVyZW5jZSB0eXBlIGNvbnN0YW50IChlLmcuLCBSRUZFUkVOQ0VfQ0hJTERfT0Ygb3JcbiAqIFJFRkVSRU5DRV9GT0xMT1dTX0ZST00pIHdpdGggdGhlIFNwYW5Db250ZXh0IGl0IHBvaW50cyB0by5cbiAqXG4gKiBTZWUgdGhlIGV4cG9ydGVkIGNoaWxkT2YoKSBhbmQgZm9sbG93c0Zyb20oKSBmdW5jdGlvbnMgYXQgdGhlIHBhY2thZ2UgbGV2ZWwuXG4gKi9cbnZhciBSZWZlcmVuY2UgPSAvKiogQGNsYXNzICovIChmdW5jdGlvbiAoKSB7XG4gICAgLyoqXG4gICAgICogSW5pdGlhbGl6ZSBhIG5ldyBSZWZlcmVuY2UgaW5zdGFuY2UuXG4gICAgICpcbiAgICAgKiBAcGFyYW0ge3N0cmluZ30gdHlwZSAtIHRoZSBSZWZlcmVuY2UgdHlwZSBjb25zdGFudCAoZS5nLixcbiAgICAgKiAgICAgICAgUkVGRVJFTkNFX0NISUxEX09GIG9yIFJFRkVSRU5DRV9GT0xMT1dTX0ZST00pLlxuICAgICAqIEBwYXJhbSB7U3BhbkNvbnRleHR9IHJlZmVyZW5jZWRDb250ZXh0IC0gdGhlIFNwYW5Db250ZXh0IGJlaW5nIHJlZmVycmVkXG4gICAgICogICAgICAgIHRvLiBBcyBhIGNvbnZlbmllbmNlLCBhIFNwYW4gaW5zdGFuY2UgbWF5IGJlIHBhc3NlZCBpbiBpbnN0ZWFkXG4gICAgICogICAgICAgIChpbiB3aGljaCBjYXNlIGl0cyAuY29udGV4dCgpIGlzIHVzZWQgaGVyZSkuXG4gICAgICovXG4gICAgZnVuY3Rpb24gUmVmZXJlbmNlKHR5cGUsIHJlZmVyZW5jZWRDb250ZXh0KSB7XG4gICAgICAgIHRoaXMuX3R5cGUgPSB0eXBlO1xuICAgICAgICB0aGlzLl9yZWZlcmVuY2VkQ29udGV4dCA9IChyZWZlcmVuY2VkQ29udGV4dCBpbnN0YW5jZW9mIHNwYW5fMS5kZWZhdWx0ID9cbiAgICAgICAgICAgIHJlZmVyZW5jZWRDb250ZXh0LmNvbnRleHQoKSA6XG4gICAgICAgICAgICByZWZlcmVuY2VkQ29udGV4dCk7XG4gICAgfVxuICAgIC8qKlxuICAgICAqIEByZXR1cm4ge3N0cmluZ30gVGhlIFJlZmVyZW5jZSB0eXBlIChlLmcuLCBSRUZFUkVOQ0VfQ0hJTERfT0Ygb3JcbiAgICAgKiAgICAgICAgIFJFRkVSRU5DRV9GT0xMT1dTX0ZST00pLlxuICAgICAqL1xuICAgIFJlZmVyZW5jZS5wcm90b3R5cGUudHlwZSA9IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgcmV0dXJuIHRoaXMuX3R5cGU7XG4gICAgfTtcbiAgICAvKipcbiAgICAgKiBAcmV0dXJuIHtTcGFuQ29udGV4dH0gVGhlIFNwYW5Db250ZXh0IGJlaW5nIHJlZmVycmVkIHRvIChlLmcuLCB0aGVcbiAgICAgKiAgICAgICAgIHBhcmVudCBpbiBhIFJFRkVSRU5DRV9DSElMRF9PRiBSZWZlcmVuY2UpLlxuICAgICAqL1xuICAgIFJlZmVyZW5jZS5wcm90b3R5cGUucmVmZXJlbmNlZENvbnRleHQgPSBmdW5jdGlvbiAoKSB7XG4gICAgICAgIHJldHVybiB0aGlzLl9yZWZlcmVuY2VkQ29udGV4dDtcbiAgICB9O1xuICAgIHJldHVybiBSZWZlcmVuY2U7XG59KCkpO1xuZXhwb3J0cy5kZWZhdWx0ID0gUmVmZXJlbmNlO1xuLy8jIHNvdXJjZU1hcHBpbmdVUkw9cmVmZXJlbmNlLmpzLm1hcCIsIlwidXNlIHN0cmljdFwiO1xuT2JqZWN0LmRlZmluZVByb3BlcnR5KGV4cG9ydHMsIFwiX19lc01vZHVsZVwiLCB7IHZhbHVlOiB0cnVlIH0pO1xudmFyIG5vb3AgPSByZXF1aXJlKFwiLi9ub29wXCIpO1xuLyoqXG4gKiBTcGFuIHJlcHJlc2VudHMgYSBsb2dpY2FsIHVuaXQgb2Ygd29yayBhcyBwYXJ0IG9mIGEgYnJvYWRlciBUcmFjZS4gRXhhbXBsZXNcbiAqIG9mIHNwYW4gbWlnaHQgaW5jbHVkZSByZW1vdGUgcHJvY2VkdXJlIGNhbGxzIG9yIGEgaW4tcHJvY2VzcyBmdW5jdGlvbiBjYWxsc1xuICogdG8gc3ViLWNvbXBvbmVudHMuIEEgVHJhY2UgaGFzIGEgc2luZ2xlLCB0b3AtbGV2ZWwgXCJyb290XCIgU3BhbiB0aGF0IGluIHR1cm5cbiAqIG1heSBoYXZlIHplcm8gb3IgbW9yZSBjaGlsZCBTcGFucywgd2hpY2ggaW4gdHVybiBtYXkgaGF2ZSBjaGlsZHJlbi5cbiAqL1xudmFyIFNwYW4gPSAvKiogQGNsYXNzICovIChmdW5jdGlvbiAoKSB7XG4gICAgZnVuY3Rpb24gU3BhbigpIHtcbiAgICB9XG4gICAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSAvL1xuICAgIC8vIE9wZW5UcmFjaW5nIEFQSSBtZXRob2RzXG4gICAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSAvL1xuICAgIC8qKlxuICAgICAqIFJldHVybnMgdGhlIFNwYW5Db250ZXh0IG9iamVjdCBhc3NvY2lhdGVkIHdpdGggdGhpcyBTcGFuLlxuICAgICAqXG4gICAgICogQHJldHVybiB7U3BhbkNvbnRleHR9XG4gICAgICovXG4gICAgU3Bhbi5wcm90b3R5cGUuY29udGV4dCA9IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgcmV0dXJuIHRoaXMuX2NvbnRleHQoKTtcbiAgICB9O1xuICAgIC8qKlxuICAgICAqIFJldHVybnMgdGhlIFRyYWNlciBvYmplY3QgdXNlZCB0byBjcmVhdGUgdGhpcyBTcGFuLlxuICAgICAqXG4gICAgICogQHJldHVybiB7VHJhY2VyfVxuICAgICAqL1xuICAgIFNwYW4ucHJvdG90eXBlLnRyYWNlciA9IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgcmV0dXJuIHRoaXMuX3RyYWNlcigpO1xuICAgIH07XG4gICAgLyoqXG4gICAgICogU2V0cyB0aGUgc3RyaW5nIG5hbWUgZm9yIHRoZSBsb2dpY2FsIG9wZXJhdGlvbiB0aGlzIHNwYW4gcmVwcmVzZW50cy5cbiAgICAgKlxuICAgICAqIEBwYXJhbSB7c3RyaW5nfSBuYW1lXG4gICAgICovXG4gICAgU3Bhbi5wcm90b3R5cGUuc2V0T3BlcmF0aW9uTmFtZSA9IGZ1bmN0aW9uIChuYW1lKSB7XG4gICAgICAgIHRoaXMuX3NldE9wZXJhdGlvbk5hbWUobmFtZSk7XG4gICAgICAgIHJldHVybiB0aGlzO1xuICAgIH07XG4gICAgLyoqXG4gICAgICogU2V0cyBhIGtleTp2YWx1ZSBwYWlyIG9uIHRoaXMgU3BhbiB0aGF0IGFsc28gcHJvcGFnYXRlcyB0byBmdXR1cmVcbiAgICAgKiBjaGlsZHJlbiBvZiB0aGUgYXNzb2NpYXRlZCBTcGFuLlxuICAgICAqXG4gICAgICogc2V0QmFnZ2FnZUl0ZW0oKSBlbmFibGVzIHBvd2VyZnVsIGZ1bmN0aW9uYWxpdHkgZ2l2ZW4gYSBmdWxsLXN0YWNrXG4gICAgICogb3BlbnRyYWNpbmcgaW50ZWdyYXRpb24gKGUuZy4sIGFyYml0cmFyeSBhcHBsaWNhdGlvbiBkYXRhIGZyb20gYSB3ZWJcbiAgICAgKiBjbGllbnQgY2FuIG1ha2UgaXQsIHRyYW5zcGFyZW50bHksIGFsbCB0aGUgd2F5IGludG8gdGhlIGRlcHRocyBvZiBhXG4gICAgICogc3RvcmFnZSBzeXN0ZW0pLCBhbmQgd2l0aCBpdCBzb21lIHBvd2VyZnVsIGNvc3RzOiB1c2UgdGhpcyBmZWF0dXJlIHdpdGhcbiAgICAgKiBjYXJlLlxuICAgICAqXG4gICAgICogSU1QT1JUQU5UIE5PVEUgIzE6IHNldEJhZ2dhZ2VJdGVtKCkgd2lsbCBvbmx5IHByb3BhZ2F0ZSBiYWdnYWdlIGl0ZW1zIHRvXG4gICAgICogKmZ1dHVyZSogY2F1c2FsIGRlc2NlbmRhbnRzIG9mIHRoZSBhc3NvY2lhdGVkIFNwYW4uXG4gICAgICpcbiAgICAgKiBJTVBPUlRBTlQgTk9URSAjMjogVXNlIHRoaXMgdGhvdWdodGZ1bGx5IGFuZCB3aXRoIGNhcmUuIEV2ZXJ5IGtleSBhbmRcbiAgICAgKiB2YWx1ZSBpcyBjb3BpZWQgaW50byBldmVyeSBsb2NhbCAqYW5kIHJlbW90ZSogY2hpbGQgb2YgdGhlIGFzc29jaWF0ZWRcbiAgICAgKiBTcGFuLCBhbmQgdGhhdCBjYW4gYWRkIHVwIHRvIGEgbG90IG9mIG5ldHdvcmsgYW5kIGNwdSBvdmVyaGVhZC5cbiAgICAgKlxuICAgICAqIEBwYXJhbSB7c3RyaW5nfSBrZXlcbiAgICAgKiBAcGFyYW0ge3N0cmluZ30gdmFsdWVcbiAgICAgKi9cbiAgICBTcGFuLnByb3RvdHlwZS5zZXRCYWdnYWdlSXRlbSA9IGZ1bmN0aW9uIChrZXksIHZhbHVlKSB7XG4gICAgICAgIHRoaXMuX3NldEJhZ2dhZ2VJdGVtKGtleSwgdmFsdWUpO1xuICAgICAgICByZXR1cm4gdGhpcztcbiAgICB9O1xuICAgIC8qKlxuICAgICAqIFJldHVybnMgdGhlIHZhbHVlIGZvciBhIGJhZ2dhZ2UgaXRlbSBnaXZlbiBpdHMga2V5LlxuICAgICAqXG4gICAgICogQHBhcmFtICB7c3RyaW5nfSBrZXlcbiAgICAgKiAgICAgICAgIFRoZSBrZXkgZm9yIHRoZSBnaXZlbiB0cmFjZSBhdHRyaWJ1dGUuXG4gICAgICogQHJldHVybiB7c3RyaW5nfVxuICAgICAqICAgICAgICAgU3RyaW5nIHZhbHVlIGZvciB0aGUgZ2l2ZW4ga2V5LCBvciB1bmRlZmluZWQgaWYgdGhlIGtleSBkb2VzIG5vdFxuICAgICAqICAgICAgICAgY29ycmVzcG9uZCB0byBhIHNldCB0cmFjZSBhdHRyaWJ1dGUuXG4gICAgICovXG4gICAgU3Bhbi5wcm90b3R5cGUuZ2V0QmFnZ2FnZUl0ZW0gPSBmdW5jdGlvbiAoa2V5KSB7XG4gICAgICAgIHJldHVybiB0aGlzLl9nZXRCYWdnYWdlSXRlbShrZXkpO1xuICAgIH07XG4gICAgLyoqXG4gICAgICogQWRkcyBhIHNpbmdsZSB0YWcgdG8gdGhlIHNwYW4uICBTZWUgYGFkZFRhZ3MoKWAgZm9yIGRldGFpbHMuXG4gICAgICpcbiAgICAgKiBAcGFyYW0ge3N0cmluZ30ga2V5XG4gICAgICogQHBhcmFtIHthbnl9IHZhbHVlXG4gICAgICovXG4gICAgU3Bhbi5wcm90b3R5cGUuc2V0VGFnID0gZnVuY3Rpb24gKGtleSwgdmFsdWUpIHtcbiAgICAgICAgLy8gTk9URTogdGhlIGNhbGwgaXMgbm9ybWFsaXplZCB0byBhIGNhbGwgdG8gX2FkZFRhZ3MoKVxuICAgICAgICB0aGlzLl9hZGRUYWdzKChfYSA9IHt9LCBfYVtrZXldID0gdmFsdWUsIF9hKSk7XG4gICAgICAgIHJldHVybiB0aGlzO1xuICAgICAgICB2YXIgX2E7XG4gICAgfTtcbiAgICAvKipcbiAgICAgKiBBZGRzIHRoZSBnaXZlbiBrZXkgdmFsdWUgcGFpcnMgdG8gdGhlIHNldCBvZiBzcGFuIHRhZ3MuXG4gICAgICpcbiAgICAgKiBNdWx0aXBsZSBjYWxscyB0byBhZGRUYWdzKCkgcmVzdWx0cyBpbiB0aGUgdGFncyBiZWluZyB0aGUgc3VwZXJzZXQgb2ZcbiAgICAgKiBhbGwgY2FsbHMuXG4gICAgICpcbiAgICAgKiBUaGUgYmVoYXZpb3Igb2Ygc2V0dGluZyB0aGUgc2FtZSBrZXkgbXVsdGlwbGUgdGltZXMgb24gdGhlIHNhbWUgc3BhblxuICAgICAqIGlzIHVuZGVmaW5lZC5cbiAgICAgKlxuICAgICAqIFRoZSBzdXBwb3J0ZWQgdHlwZSBvZiB0aGUgdmFsdWVzIGlzIGltcGxlbWVudGF0aW9uLWRlcGVuZGVudC5cbiAgICAgKiBJbXBsZW1lbnRhdGlvbnMgYXJlIGV4cGVjdGVkIHRvIHNhZmVseSBoYW5kbGUgYWxsIHR5cGVzIG9mIHZhbHVlcyBidXRcbiAgICAgKiBtYXkgY2hvb3NlIHRvIGlnbm9yZSB1bnJlY29nbml6ZWQgLyB1bmhhbmRsZS1hYmxlIHZhbHVlcyAoZS5nLiBvYmplY3RzXG4gICAgICogd2l0aCBjeWNsaWMgcmVmZXJlbmNlcywgZnVuY3Rpb24gb2JqZWN0cykuXG4gICAgICpcbiAgICAgKiBAcmV0dXJuIHtbdHlwZV19IFtkZXNjcmlwdGlvbl1cbiAgICAgKi9cbiAgICBTcGFuLnByb3RvdHlwZS5hZGRUYWdzID0gZnVuY3Rpb24gKGtleVZhbHVlTWFwKSB7XG4gICAgICAgIHRoaXMuX2FkZFRhZ3Moa2V5VmFsdWVNYXApO1xuICAgICAgICByZXR1cm4gdGhpcztcbiAgICB9O1xuICAgIC8qKlxuICAgICAqIEFkZCBhIGxvZyByZWNvcmQgdG8gdGhpcyBTcGFuLCBvcHRpb25hbGx5IGF0IGEgdXNlci1wcm92aWRlZCB0aW1lc3RhbXAuXG4gICAgICpcbiAgICAgKiBGb3IgZXhhbXBsZTpcbiAgICAgKlxuICAgICAqICAgICBzcGFuLmxvZyh7XG4gICAgICogICAgICAgICBzaXplOiBycGMuc2l6ZSgpLCAgLy8gbnVtZXJpYyB2YWx1ZVxuICAgICAqICAgICAgICAgVVJJOiBycGMuVVJJKCksICAvLyBzdHJpbmcgdmFsdWVcbiAgICAgKiAgICAgICAgIHBheWxvYWQ6IHJwYy5wYXlsb2FkKCksICAvLyBPYmplY3QgdmFsdWVcbiAgICAgKiAgICAgICAgIFwia2V5cyBjYW4gYmUgYXJiaXRyYXJ5IHN0cmluZ3NcIjogcnBjLmZvbygpLFxuICAgICAqICAgICB9KTtcbiAgICAgKlxuICAgICAqICAgICBzcGFuLmxvZyh7XG4gICAgICogICAgICAgICBcImVycm9yLmRlc2NyaXB0aW9uXCI6IHNvbWVFcnJvci5kZXNjcmlwdGlvbigpLFxuICAgICAqICAgICB9LCBzb21lRXJyb3IudGltZXN0YW1wTWlsbGlzKCkpO1xuICAgICAqXG4gICAgICogQHBhcmFtIHtvYmplY3R9IGtleVZhbHVlUGFpcnNcbiAgICAgKiAgICAgICAgQW4gb2JqZWN0IG1hcHBpbmcgc3RyaW5nIGtleXMgdG8gYXJiaXRyYXJ5IHZhbHVlIHR5cGVzLiBBbGxcbiAgICAgKiAgICAgICAgVHJhY2VyIGltcGxlbWVudGF0aW9ucyBzaG91bGQgc3VwcG9ydCBib29sLCBzdHJpbmcsIGFuZCBudW1lcmljXG4gICAgICogICAgICAgIHZhbHVlIHR5cGVzLCBhbmQgc29tZSBtYXkgYWxzbyBzdXBwb3J0IE9iamVjdCB2YWx1ZXMuXG4gICAgICogQHBhcmFtIHtudW1iZXJ9IHRpbWVzdGFtcFxuICAgICAqICAgICAgICBBbiBvcHRpb25hbCBwYXJhbWV0ZXIgc3BlY2lmeWluZyB0aGUgdGltZXN0YW1wIGluIG1pbGxpc2Vjb25kc1xuICAgICAqICAgICAgICBzaW5jZSB0aGUgVW5peCBlcG9jaC4gRnJhY3Rpb25hbCB2YWx1ZXMgYXJlIGFsbG93ZWQgc28gdGhhdFxuICAgICAqICAgICAgICB0aW1lc3RhbXBzIHdpdGggc3ViLW1pbGxpc2Vjb25kIGFjY3VyYWN5IGNhbiBiZSByZXByZXNlbnRlZC4gSWZcbiAgICAgKiAgICAgICAgbm90IHNwZWNpZmllZCwgdGhlIGltcGxlbWVudGF0aW9uIGlzIGV4cGVjdGVkIHRvIHVzZSBpdHMgbm90aW9uXG4gICAgICogICAgICAgIG9mIHRoZSBjdXJyZW50IHRpbWUgb2YgdGhlIGNhbGwuXG4gICAgICovXG4gICAgU3Bhbi5wcm90b3R5cGUubG9nID0gZnVuY3Rpb24gKGtleVZhbHVlUGFpcnMsIHRpbWVzdGFtcCkge1xuICAgICAgICB0aGlzLl9sb2coa2V5VmFsdWVQYWlycywgdGltZXN0YW1wKTtcbiAgICAgICAgcmV0dXJuIHRoaXM7XG4gICAgfTtcbiAgICAvKipcbiAgICAgKiBERVBSRUNBVEVEXG4gICAgICovXG4gICAgU3Bhbi5wcm90b3R5cGUubG9nRXZlbnQgPSBmdW5jdGlvbiAoZXZlbnROYW1lLCBwYXlsb2FkKSB7XG4gICAgICAgIHJldHVybiB0aGlzLl9sb2coeyBldmVudDogZXZlbnROYW1lLCBwYXlsb2FkOiBwYXlsb2FkIH0pO1xuICAgIH07XG4gICAgLyoqXG4gICAgICogU2V0cyB0aGUgZW5kIHRpbWVzdGFtcCBhbmQgZmluYWxpemVzIFNwYW4gc3RhdGUuXG4gICAgICpcbiAgICAgKiBXaXRoIHRoZSBleGNlcHRpb24gb2YgY2FsbHMgdG8gU3Bhbi5jb250ZXh0KCkgKHdoaWNoIGFyZSBhbHdheXMgYWxsb3dlZCksXG4gICAgICogZmluaXNoKCkgbXVzdCBiZSB0aGUgbGFzdCBjYWxsIG1hZGUgdG8gYW55IHNwYW4gaW5zdGFuY2UsIGFuZCB0byBkb1xuICAgICAqIG90aGVyd2lzZSBsZWFkcyB0byB1bmRlZmluZWQgYmVoYXZpb3IuXG4gICAgICpcbiAgICAgKiBAcGFyYW0gIHtudW1iZXJ9IGZpbmlzaFRpbWVcbiAgICAgKiAgICAgICAgIE9wdGlvbmFsIGZpbmlzaCB0aW1lIGluIG1pbGxpc2Vjb25kcyBhcyBhIFVuaXggdGltZXN0YW1wLiBEZWNpbWFsXG4gICAgICogICAgICAgICB2YWx1ZXMgYXJlIHN1cHBvcnRlZCBmb3IgdGltZXN0YW1wcyB3aXRoIHN1Yi1taWxsaXNlY29uZCBhY2N1cmFjeS5cbiAgICAgKiAgICAgICAgIElmIG5vdCBzcGVjaWZpZWQsIHRoZSBjdXJyZW50IHRpbWUgKGFzIGRlZmluZWQgYnkgdGhlXG4gICAgICogICAgICAgICBpbXBsZW1lbnRhdGlvbikgd2lsbCBiZSB1c2VkLlxuICAgICAqL1xuICAgIFNwYW4ucHJvdG90eXBlLmZpbmlzaCA9IGZ1bmN0aW9uIChmaW5pc2hUaW1lKSB7XG4gICAgICAgIHRoaXMuX2ZpbmlzaChmaW5pc2hUaW1lKTtcbiAgICAgICAgLy8gRG8gbm90IHJldHVybiBgdGhpc2AuIFRoZSBTcGFuIGdlbmVyYWxseSBzaG91bGQgbm90IGJlIHVzZWQgYWZ0ZXIgaXRcbiAgICAgICAgLy8gaXMgZmluaXNoZWQgc28gY2hhaW5pbmcgaXMgbm90IGRlc2lyZWQgaW4gdGhpcyBjb250ZXh0LlxuICAgIH07XG4gICAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSAvL1xuICAgIC8vIERlcml2ZWQgY2xhc3NlcyBjYW4gY2hvb3NlIHRvIGltcGxlbWVudCB0aGUgYmVsb3dcbiAgICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIC8vXG4gICAgLy8gQnkgZGVmYXVsdCByZXR1cm5zIGEgbm8tb3AgU3BhbkNvbnRleHQuXG4gICAgU3Bhbi5wcm90b3R5cGUuX2NvbnRleHQgPSBmdW5jdGlvbiAoKSB7XG4gICAgICAgIHJldHVybiBub29wLnNwYW5Db250ZXh0O1xuICAgIH07XG4gICAgLy8gQnkgZGVmYXVsdCByZXR1cm5zIGEgbm8tb3AgdHJhY2VyLlxuICAgIC8vXG4gICAgLy8gVGhlIGJhc2UgY2xhc3MgY291bGQgc3RvcmUgdGhlIHRyYWNlciB0aGF0IGNyZWF0ZWQgaXQsIGJ1dCBpdCBkb2VzIG5vdFxuICAgIC8vIGluIG9yZGVyIHRvIGVuc3VyZSB0aGUgbm8tb3Agc3BhbiBpbXBsZW1lbnRhdGlvbiBoYXMgemVybyBtZW1iZXJzLFxuICAgIC8vIHdoaWNoIGFsbG93cyBWOCB0byBhZ2dyZXNzaXZlbHkgb3B0aW1pemUgY2FsbHMgdG8gc3VjaCBvYmplY3RzLlxuICAgIFNwYW4ucHJvdG90eXBlLl90cmFjZXIgPSBmdW5jdGlvbiAoKSB7XG4gICAgICAgIHJldHVybiBub29wLnRyYWNlcjtcbiAgICB9O1xuICAgIC8vIEJ5IGRlZmF1bHQgZG9lcyBub3RoaW5nXG4gICAgU3Bhbi5wcm90b3R5cGUuX3NldE9wZXJhdGlvbk5hbWUgPSBmdW5jdGlvbiAobmFtZSkge1xuICAgIH07XG4gICAgLy8gQnkgZGVmYXVsdCBkb2VzIG5vdGhpbmdcbiAgICBTcGFuLnByb3RvdHlwZS5fc2V0QmFnZ2FnZUl0ZW0gPSBmdW5jdGlvbiAoa2V5LCB2YWx1ZSkge1xuICAgIH07XG4gICAgLy8gQnkgZGVmYXVsdCBkb2VzIG5vdGhpbmdcbiAgICBTcGFuLnByb3RvdHlwZS5fZ2V0QmFnZ2FnZUl0ZW0gPSBmdW5jdGlvbiAoa2V5KSB7XG4gICAgICAgIHJldHVybiB1bmRlZmluZWQ7XG4gICAgfTtcbiAgICAvLyBCeSBkZWZhdWx0IGRvZXMgbm90aGluZ1xuICAgIC8vXG4gICAgLy8gTk9URTogYm90aCBzZXRUYWcoKSBhbmQgYWRkVGFncygpIG1hcCB0byB0aGlzIGZ1bmN0aW9uLiBrZXlWYWx1ZVBhaXJzXG4gICAgLy8gd2lsbCBhbHdheXMgYmUgYW4gYXNzb2NpYXRpdmUgYXJyYXkuXG4gICAgU3Bhbi5wcm90b3R5cGUuX2FkZFRhZ3MgPSBmdW5jdGlvbiAoa2V5VmFsdWVQYWlycykge1xuICAgIH07XG4gICAgLy8gQnkgZGVmYXVsdCBkb2VzIG5vdGhpbmdcbiAgICBTcGFuLnByb3RvdHlwZS5fbG9nID0gZnVuY3Rpb24gKGtleVZhbHVlUGFpcnMsIHRpbWVzdGFtcCkge1xuICAgIH07XG4gICAgLy8gQnkgZGVmYXVsdCBkb2VzIG5vdGhpbmdcbiAgICAvL1xuICAgIC8vIGZpbmlzaFRpbWUgaXMgZXhwZWN0ZWQgdG8gYmUgZWl0aGVyIGEgbnVtYmVyIG9yIHVuZGVmaW5lZC5cbiAgICBTcGFuLnByb3RvdHlwZS5fZmluaXNoID0gZnVuY3Rpb24gKGZpbmlzaFRpbWUpIHtcbiAgICB9O1xuICAgIHJldHVybiBTcGFuO1xufSgpKTtcbmV4cG9ydHMuU3BhbiA9IFNwYW47XG5leHBvcnRzLmRlZmF1bHQgPSBTcGFuO1xuLy8jIHNvdXJjZU1hcHBpbmdVUkw9c3Bhbi5qcy5tYXAiLCJcInVzZSBzdHJpY3RcIjtcbk9iamVjdC5kZWZpbmVQcm9wZXJ0eShleHBvcnRzLCBcIl9fZXNNb2R1bGVcIiwgeyB2YWx1ZTogdHJ1ZSB9KTtcbi8qKlxuICogU3BhbkNvbnRleHQgcmVwcmVzZW50cyBTcGFuIHN0YXRlIHRoYXQgbXVzdCBwcm9wYWdhdGUgdG8gZGVzY2VuZGFudCBTcGFuc1xuICogYW5kIGFjcm9zcyBwcm9jZXNzIGJvdW5kYXJpZXMuXG4gKlxuICogU3BhbkNvbnRleHQgaXMgbG9naWNhbGx5IGRpdmlkZWQgaW50byB0d28gcGllY2VzOiB0aGUgdXNlci1sZXZlbCBcIkJhZ2dhZ2VcIlxuICogKHNlZSBzZXRCYWdnYWdlSXRlbSBhbmQgZ2V0QmFnZ2FnZUl0ZW0pIHRoYXQgcHJvcGFnYXRlcyBhY3Jvc3MgU3BhblxuICogYm91bmRhcmllcyBhbmQgYW55IFRyYWNlci1pbXBsZW1lbnRhdGlvbi1zcGVjaWZpYyBmaWVsZHMgdGhhdCBhcmUgbmVlZGVkIHRvXG4gKiBpZGVudGlmeSBvciBvdGhlcndpc2UgY29udGV4dHVhbGl6ZSB0aGUgYXNzb2NpYXRlZCBTcGFuIGluc3RhbmNlIChlLmcuLCBhXG4gKiA8dHJhY2VfaWQsIHNwYW5faWQsIHNhbXBsZWQ+IHR1cGxlKS5cbiAqL1xudmFyIFNwYW5Db250ZXh0ID0gLyoqIEBjbGFzcyAqLyAoZnVuY3Rpb24gKCkge1xuICAgIGZ1bmN0aW9uIFNwYW5Db250ZXh0KCkge1xuICAgIH1cbiAgICByZXR1cm4gU3BhbkNvbnRleHQ7XG59KCkpO1xuZXhwb3J0cy5TcGFuQ29udGV4dCA9IFNwYW5Db250ZXh0O1xuZXhwb3J0cy5kZWZhdWx0ID0gU3BhbkNvbnRleHQ7XG4vLyMgc291cmNlTWFwcGluZ1VSTD1zcGFuX2NvbnRleHQuanMubWFwIiwiXCJ1c2Ugc3RyaWN0XCI7XG5PYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgXCJfX2VzTW9kdWxlXCIsIHsgdmFsdWU6IHRydWUgfSk7XG52YXIgRnVuY3Rpb25zID0gcmVxdWlyZShcIi4vZnVuY3Rpb25zXCIpO1xudmFyIE5vb3AgPSByZXF1aXJlKFwiLi9ub29wXCIpO1xudmFyIHNwYW5fMSA9IHJlcXVpcmUoXCIuL3NwYW5cIik7XG4vKipcbiAqIFRyYWNlciBpcyB0aGUgZW50cnktcG9pbnQgYmV0d2VlbiB0aGUgaW5zdHJ1bWVudGF0aW9uIEFQSSBhbmQgdGhlIHRyYWNpbmdcbiAqIGltcGxlbWVudGF0aW9uLlxuICpcbiAqIFRoZSBkZWZhdWx0IG9iamVjdCBhY3RzIGFzIGEgbm8tb3AgaW1wbGVtZW50YXRpb24uXG4gKlxuICogTm90ZSB0byBpbXBsZW1lbnRhdG9yczogZGVyaXZlZCBjbGFzc2VzIGNhbiBjaG9vc2UgdG8gZGlyZWN0bHkgaW1wbGVtZW50IHRoZVxuICogbWV0aG9kcyBpbiB0aGUgXCJPcGVuVHJhY2luZyBBUEkgbWV0aG9kc1wiIHNlY3Rpb24sIG9yIG9wdGlvbmFsbHkgdGhlIHN1YnNldCBvZlxuICogdW5kZXJzY29yZS1wcmVmaXhlZCBtZXRob2RzIHRvIHBpY2sgdXAgdGhlIGFyZ3VtZW50IGNoZWNraW5nIGFuZCBoYW5kbGluZ1xuICogYXV0b21hdGljYWxseSBmcm9tIHRoZSBiYXNlIGNsYXNzLlxuICovXG52YXIgVHJhY2VyID0gLyoqIEBjbGFzcyAqLyAoZnVuY3Rpb24gKCkge1xuICAgIGZ1bmN0aW9uIFRyYWNlcigpIHtcbiAgICB9XG4gICAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSAvL1xuICAgIC8vIE9wZW5UcmFjaW5nIEFQSSBtZXRob2RzXG4gICAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSAvL1xuICAgIC8qKlxuICAgICAqIFN0YXJ0cyBhbmQgcmV0dXJucyBhIG5ldyBTcGFuIHJlcHJlc2VudGluZyBhIGxvZ2ljYWwgdW5pdCBvZiB3b3JrLlxuICAgICAqXG4gICAgICogRm9yIGV4YW1wbGU6XG4gICAgICpcbiAgICAgKiAgICAgLy8gU3RhcnQgYSBuZXcgKHBhcmVudGxlc3MpIHJvb3QgU3BhbjpcbiAgICAgKiAgICAgdmFyIHBhcmVudCA9IFRyYWNlci5zdGFydFNwYW4oJ0RvV29yaycpO1xuICAgICAqXG4gICAgICogICAgIC8vIFN0YXJ0IGEgbmV3IChjaGlsZCkgU3BhbjpcbiAgICAgKiAgICAgdmFyIGNoaWxkID0gVHJhY2VyLnN0YXJ0U3BhbignbG9hZC1mcm9tLWRiJywge1xuICAgICAqICAgICAgICAgY2hpbGRPZjogcGFyZW50LmNvbnRleHQoKSxcbiAgICAgKiAgICAgfSk7XG4gICAgICpcbiAgICAgKiAgICAgLy8gU3RhcnQgYSBuZXcgYXN5bmMgKEZvbGxvd3NGcm9tKSBTcGFuOlxuICAgICAqICAgICB2YXIgY2hpbGQgPSBUcmFjZXIuc3RhcnRTcGFuKCdhc3luYy1jYWNoZS13cml0ZScsIHtcbiAgICAgKiAgICAgICAgIHJlZmVyZW5jZXM6IFtcbiAgICAgKiAgICAgICAgICAgICBvcGVudHJhY2luZy5mb2xsb3dzRnJvbShwYXJlbnQuY29udGV4dCgpKVxuICAgICAqICAgICAgICAgXSxcbiAgICAgKiAgICAgfSk7XG4gICAgICpcbiAgICAgKiBAcGFyYW0ge3N0cmluZ30gbmFtZSAtIHRoZSBuYW1lIG9mIHRoZSBvcGVyYXRpb24gKFJFUVVJUkVEKS5cbiAgICAgKiBAcGFyYW0ge1NwYW5PcHRpb25zfSBbb3B0aW9uc10gLSBvcHRpb25zIGZvciB0aGUgbmV3bHkgY3JlYXRlZCBzcGFuLlxuICAgICAqIEByZXR1cm4ge1NwYW59IC0gYSBuZXcgU3BhbiBvYmplY3QuXG4gICAgICovXG4gICAgVHJhY2VyLnByb3RvdHlwZS5zdGFydFNwYW4gPSBmdW5jdGlvbiAobmFtZSwgb3B0aW9ucykge1xuICAgICAgICBpZiAob3B0aW9ucyA9PT0gdm9pZCAwKSB7IG9wdGlvbnMgPSB7fTsgfVxuICAgICAgICAvLyBDb252ZXJ0IG9wdGlvbnMuY2hpbGRPZiB0byBmaWVsZHMucmVmZXJlbmNlcyBhcyBuZWVkZWQuXG4gICAgICAgIGlmIChvcHRpb25zLmNoaWxkT2YpIHtcbiAgICAgICAgICAgIC8vIENvbnZlcnQgZnJvbSBhIFNwYW4gb3IgYSBTcGFuQ29udGV4dCBpbnRvIGEgUmVmZXJlbmNlLlxuICAgICAgICAgICAgdmFyIGNoaWxkT2YgPSBGdW5jdGlvbnMuY2hpbGRPZihvcHRpb25zLmNoaWxkT2YpO1xuICAgICAgICAgICAgaWYgKG9wdGlvbnMucmVmZXJlbmNlcykge1xuICAgICAgICAgICAgICAgIG9wdGlvbnMucmVmZXJlbmNlcy5wdXNoKGNoaWxkT2YpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgZWxzZSB7XG4gICAgICAgICAgICAgICAgb3B0aW9ucy5yZWZlcmVuY2VzID0gW2NoaWxkT2ZdO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgZGVsZXRlIChvcHRpb25zLmNoaWxkT2YpO1xuICAgICAgICB9XG4gICAgICAgIHJldHVybiB0aGlzLl9zdGFydFNwYW4obmFtZSwgb3B0aW9ucyk7XG4gICAgfTtcbiAgICAvKipcbiAgICAgKiBJbmplY3RzIHRoZSBnaXZlbiBTcGFuQ29udGV4dCBpbnN0YW5jZSBmb3IgY3Jvc3MtcHJvY2VzcyBwcm9wYWdhdGlvblxuICAgICAqIHdpdGhpbiBgY2FycmllcmAuIFRoZSBleHBlY3RlZCB0eXBlIG9mIGBjYXJyaWVyYCBkZXBlbmRzIG9uIHRoZSB2YWx1ZSBvZlxuICAgICAqIGBmb3JtYXQuXG4gICAgICpcbiAgICAgKiBPcGVuVHJhY2luZyBkZWZpbmVzIGEgY29tbW9uIHNldCBvZiBgZm9ybWF0YCB2YWx1ZXMgKHNlZVxuICAgICAqIEZPUk1BVF9URVhUX01BUCwgRk9STUFUX0hUVFBfSEVBREVSUywgYW5kIEZPUk1BVF9CSU5BUlkpLCBhbmQgZWFjaCBoYXNcbiAgICAgKiBhbiBleHBlY3RlZCBjYXJyaWVyIHR5cGUuXG4gICAgICpcbiAgICAgKiBDb25zaWRlciB0aGlzIHBzZXVkb2NvZGUgZXhhbXBsZTpcbiAgICAgKlxuICAgICAqICAgICB2YXIgY2xpZW50U3BhbiA9IC4uLjtcbiAgICAgKiAgICAgLi4uXG4gICAgICogICAgIC8vIEluamVjdCBjbGllbnRTcGFuIGludG8gYSB0ZXh0IGNhcnJpZXIuXG4gICAgICogICAgIHZhciBoZWFkZXJzQ2FycmllciA9IHt9O1xuICAgICAqICAgICBUcmFjZXIuaW5qZWN0KGNsaWVudFNwYW4uY29udGV4dCgpLCBUcmFjZXIuRk9STUFUX0hUVFBfSEVBREVSUywgaGVhZGVyc0NhcnJpZXIpO1xuICAgICAqICAgICAvLyBJbmNvcnBvcmF0ZSB0aGUgdGV4dENhcnJpZXIgaW50byB0aGUgb3V0Ym91bmQgSFRUUCByZXF1ZXN0IGhlYWRlclxuICAgICAqICAgICAvLyBtYXAuXG4gICAgICogICAgIE9iamVjdC5hc3NpZ24ob3V0Ym91bmRIVFRQUmVxLmhlYWRlcnMsIGhlYWRlcnNDYXJyaWVyKTtcbiAgICAgKiAgICAgLy8gLi4uIHNlbmQgdGhlIGh0dHBSZXFcbiAgICAgKlxuICAgICAqIEBwYXJhbSAge1NwYW5Db250ZXh0fSBzcGFuQ29udGV4dCAtIHRoZSBTcGFuQ29udGV4dCB0byBpbmplY3QgaW50byB0aGVcbiAgICAgKiAgICAgICAgIGNhcnJpZXIgb2JqZWN0LiBBcyBhIGNvbnZlbmllbmNlLCBhIFNwYW4gaW5zdGFuY2UgbWF5IGJlIHBhc3NlZFxuICAgICAqICAgICAgICAgaW4gaW5zdGVhZCAoaW4gd2hpY2ggY2FzZSBpdHMgLmNvbnRleHQoKSBpcyB1c2VkIGZvciB0aGVcbiAgICAgKiAgICAgICAgIGluamVjdCgpKS5cbiAgICAgKiBAcGFyYW0gIHtzdHJpbmd9IGZvcm1hdCAtIHRoZSBmb3JtYXQgb2YgdGhlIGNhcnJpZXIuXG4gICAgICogQHBhcmFtICB7YW55fSBjYXJyaWVyIC0gc2VlIHRoZSBkb2N1bWVudGF0aW9uIGZvciB0aGUgY2hvc2VuIGBmb3JtYXRgXG4gICAgICogICAgICAgICBmb3IgYSBkZXNjcmlwdGlvbiBvZiB0aGUgY2FycmllciBvYmplY3QuXG4gICAgICovXG4gICAgVHJhY2VyLnByb3RvdHlwZS5pbmplY3QgPSBmdW5jdGlvbiAoc3BhbkNvbnRleHQsIGZvcm1hdCwgY2Fycmllcikge1xuICAgICAgICAvLyBBbGxvdyB0aGUgdXNlciB0byBwYXNzIGEgU3BhbiBpbnN0ZWFkIG9mIGEgU3BhbkNvbnRleHRcbiAgICAgICAgaWYgKHNwYW5Db250ZXh0IGluc3RhbmNlb2Ygc3Bhbl8xLmRlZmF1bHQpIHtcbiAgICAgICAgICAgIHNwYW5Db250ZXh0ID0gc3BhbkNvbnRleHQuY29udGV4dCgpO1xuICAgICAgICB9XG4gICAgICAgIHJldHVybiB0aGlzLl9pbmplY3Qoc3BhbkNvbnRleHQsIGZvcm1hdCwgY2Fycmllcik7XG4gICAgfTtcbiAgICAvKipcbiAgICAgKiBSZXR1cm5zIGEgU3BhbkNvbnRleHQgaW5zdGFuY2UgZXh0cmFjdGVkIGZyb20gYGNhcnJpZXJgIGluIHRoZSBnaXZlblxuICAgICAqIGBmb3JtYXRgLlxuICAgICAqXG4gICAgICogT3BlblRyYWNpbmcgZGVmaW5lcyBhIGNvbW1vbiBzZXQgb2YgYGZvcm1hdGAgdmFsdWVzIChzZWVcbiAgICAgKiBGT1JNQVRfVEVYVF9NQVAsIEZPUk1BVF9IVFRQX0hFQURFUlMsIGFuZCBGT1JNQVRfQklOQVJZKSwgYW5kIGVhY2ggaGFzXG4gICAgICogYW4gZXhwZWN0ZWQgY2FycmllciB0eXBlLlxuICAgICAqXG4gICAgICogQ29uc2lkZXIgdGhpcyBwc2V1ZG9jb2RlIGV4YW1wbGU6XG4gICAgICpcbiAgICAgKiAgICAgLy8gVXNlIHRoZSBpbmJvdW5kIEhUVFAgcmVxdWVzdCdzIGhlYWRlcnMgYXMgYSB0ZXh0IG1hcCBjYXJyaWVyLlxuICAgICAqICAgICB2YXIgaGVhZGVyc0NhcnJpZXIgPSBpbmJvdW5kSFRUUFJlcS5oZWFkZXJzO1xuICAgICAqICAgICB2YXIgd2lyZUN0eCA9IFRyYWNlci5leHRyYWN0KFRyYWNlci5GT1JNQVRfSFRUUF9IRUFERVJTLCBoZWFkZXJzQ2Fycmllcik7XG4gICAgICogICAgIHZhciBzZXJ2ZXJTcGFuID0gVHJhY2VyLnN0YXJ0U3BhbignLi4uJywgeyBjaGlsZE9mIDogd2lyZUN0eCB9KTtcbiAgICAgKlxuICAgICAqIEBwYXJhbSAge3N0cmluZ30gZm9ybWF0IC0gdGhlIGZvcm1hdCBvZiB0aGUgY2Fycmllci5cbiAgICAgKiBAcGFyYW0gIHthbnl9IGNhcnJpZXIgLSB0aGUgdHlwZSBvZiB0aGUgY2FycmllciBvYmplY3QgaXMgZGV0ZXJtaW5lZCBieVxuICAgICAqICAgICAgICAgdGhlIGZvcm1hdC5cbiAgICAgKiBAcmV0dXJuIHtTcGFuQ29udGV4dH1cbiAgICAgKiAgICAgICAgIFRoZSBleHRyYWN0ZWQgU3BhbkNvbnRleHQsIG9yIG51bGwgaWYgbm8gc3VjaCBTcGFuQ29udGV4dCBjb3VsZFxuICAgICAqICAgICAgICAgYmUgZm91bmQgaW4gYGNhcnJpZXJgXG4gICAgICovXG4gICAgVHJhY2VyLnByb3RvdHlwZS5leHRyYWN0ID0gZnVuY3Rpb24gKGZvcm1hdCwgY2Fycmllcikge1xuICAgICAgICByZXR1cm4gdGhpcy5fZXh0cmFjdChmb3JtYXQsIGNhcnJpZXIpO1xuICAgIH07XG4gICAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLSAvL1xuICAgIC8vIERlcml2ZWQgY2xhc3NlcyBjYW4gY2hvb3NlIHRvIGltcGxlbWVudCB0aGUgYmVsb3dcbiAgICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tIC8vXG4gICAgLy8gTk9URTogdGhlIGlucHV0IHRvIHRoaXMgbWV0aG9kIGlzICphbHdheXMqIGFuIGFzc29jaWF0aXZlIGFycmF5LiBUaGVcbiAgICAvLyBwdWJsaWMtZmFjaW5nIHN0YXJ0U3BhbigpIG1ldGhvZCBub3JtYWxpemVzIHRoZSBhcmd1bWVudHMgc28gdGhhdFxuICAgIC8vIGFsbCBOIGltcGxlbWVudGF0aW9ucyBkbyBub3QgbmVlZCB0byB3b3JyeSBhYm91dCB2YXJpYXRpb25zIGluIHRoZSBjYWxsXG4gICAgLy8gc2lnbmF0dXJlLlxuICAgIC8vXG4gICAgLy8gVGhlIGRlZmF1bHQgYmVoYXZpb3IgcmV0dXJucyBhIG5vLW9wIHNwYW4uXG4gICAgVHJhY2VyLnByb3RvdHlwZS5fc3RhcnRTcGFuID0gZnVuY3Rpb24gKG5hbWUsIGZpZWxkcykge1xuICAgICAgICByZXR1cm4gTm9vcC5zcGFuO1xuICAgIH07XG4gICAgLy8gVGhlIGRlZmF1bHQgYmVoYXZpb3IgaXMgYSBuby1vcC5cbiAgICBUcmFjZXIucHJvdG90eXBlLl9pbmplY3QgPSBmdW5jdGlvbiAoc3BhbkNvbnRleHQsIGZvcm1hdCwgY2Fycmllcikge1xuICAgIH07XG4gICAgLy8gVGhlIGRlZmF1bHQgYmVoYXZpb3IgaXMgdG8gcmV0dXJuIGEgbm8tb3AgU3BhbkNvbnRleHQuXG4gICAgVHJhY2VyLnByb3RvdHlwZS5fZXh0cmFjdCA9IGZ1bmN0aW9uIChmb3JtYXQsIGNhcnJpZXIpIHtcbiAgICAgICAgcmV0dXJuIE5vb3Auc3BhbkNvbnRleHQ7XG4gICAgfTtcbiAgICByZXR1cm4gVHJhY2VyO1xufSgpKTtcbmV4cG9ydHMuVHJhY2VyID0gVHJhY2VyO1xuZXhwb3J0cy5kZWZhdWx0ID0gVHJhY2VyO1xuLy8jIHNvdXJjZU1hcHBpbmdVUkw9dHJhY2VyLmpzLm1hcCIsIi8qKlxuICogQHRoaXMge1Byb21pc2V9XG4gKi9cbmZ1bmN0aW9uIGZpbmFsbHlDb25zdHJ1Y3RvcihjYWxsYmFjaykge1xuICB2YXIgY29uc3RydWN0b3IgPSB0aGlzLmNvbnN0cnVjdG9yO1xuICByZXR1cm4gdGhpcy50aGVuKFxuICAgIGZ1bmN0aW9uKHZhbHVlKSB7XG4gICAgICAvLyBAdHMtaWdub3JlXG4gICAgICByZXR1cm4gY29uc3RydWN0b3IucmVzb2x2ZShjYWxsYmFjaygpKS50aGVuKGZ1bmN0aW9uKCkge1xuICAgICAgICByZXR1cm4gdmFsdWU7XG4gICAgICB9KTtcbiAgICB9LFxuICAgIGZ1bmN0aW9uKHJlYXNvbikge1xuICAgICAgLy8gQHRzLWlnbm9yZVxuICAgICAgcmV0dXJuIGNvbnN0cnVjdG9yLnJlc29sdmUoY2FsbGJhY2soKSkudGhlbihmdW5jdGlvbigpIHtcbiAgICAgICAgLy8gQHRzLWlnbm9yZVxuICAgICAgICByZXR1cm4gY29uc3RydWN0b3IucmVqZWN0KHJlYXNvbik7XG4gICAgICB9KTtcbiAgICB9XG4gICk7XG59XG5cbmV4cG9ydCBkZWZhdWx0IGZpbmFsbHlDb25zdHJ1Y3RvcjtcbiIsImltcG9ydCBwcm9taXNlRmluYWxseSBmcm9tICcuL2ZpbmFsbHknO1xuXG4vLyBTdG9yZSBzZXRUaW1lb3V0IHJlZmVyZW5jZSBzbyBwcm9taXNlLXBvbHlmaWxsIHdpbGwgYmUgdW5hZmZlY3RlZCBieVxuLy8gb3RoZXIgY29kZSBtb2RpZnlpbmcgc2V0VGltZW91dCAobGlrZSBzaW5vbi51c2VGYWtlVGltZXJzKCkpXG52YXIgc2V0VGltZW91dEZ1bmMgPSBzZXRUaW1lb3V0O1xuXG5mdW5jdGlvbiBpc0FycmF5KHgpIHtcbiAgcmV0dXJuIEJvb2xlYW4oeCAmJiB0eXBlb2YgeC5sZW5ndGggIT09ICd1bmRlZmluZWQnKTtcbn1cblxuZnVuY3Rpb24gbm9vcCgpIHt9XG5cbi8vIFBvbHlmaWxsIGZvciBGdW5jdGlvbi5wcm90b3R5cGUuYmluZFxuZnVuY3Rpb24gYmluZChmbiwgdGhpc0FyZykge1xuICByZXR1cm4gZnVuY3Rpb24oKSB7XG4gICAgZm4uYXBwbHkodGhpc0FyZywgYXJndW1lbnRzKTtcbiAgfTtcbn1cblxuLyoqXG4gKiBAY29uc3RydWN0b3JcbiAqIEBwYXJhbSB7RnVuY3Rpb259IGZuXG4gKi9cbmZ1bmN0aW9uIFByb21pc2UoZm4pIHtcbiAgaWYgKCEodGhpcyBpbnN0YW5jZW9mIFByb21pc2UpKVxuICAgIHRocm93IG5ldyBUeXBlRXJyb3IoJ1Byb21pc2VzIG11c3QgYmUgY29uc3RydWN0ZWQgdmlhIG5ldycpO1xuICBpZiAodHlwZW9mIGZuICE9PSAnZnVuY3Rpb24nKSB0aHJvdyBuZXcgVHlwZUVycm9yKCdub3QgYSBmdW5jdGlvbicpO1xuICAvKiogQHR5cGUgeyFudW1iZXJ9ICovXG4gIHRoaXMuX3N0YXRlID0gMDtcbiAgLyoqIEB0eXBlIHshYm9vbGVhbn0gKi9cbiAgdGhpcy5faGFuZGxlZCA9IGZhbHNlO1xuICAvKiogQHR5cGUge1Byb21pc2V8dW5kZWZpbmVkfSAqL1xuICB0aGlzLl92YWx1ZSA9IHVuZGVmaW5lZDtcbiAgLyoqIEB0eXBlIHshQXJyYXk8IUZ1bmN0aW9uPn0gKi9cbiAgdGhpcy5fZGVmZXJyZWRzID0gW107XG5cbiAgZG9SZXNvbHZlKGZuLCB0aGlzKTtcbn1cblxuZnVuY3Rpb24gaGFuZGxlKHNlbGYsIGRlZmVycmVkKSB7XG4gIHdoaWxlIChzZWxmLl9zdGF0ZSA9PT0gMykge1xuICAgIHNlbGYgPSBzZWxmLl92YWx1ZTtcbiAgfVxuICBpZiAoc2VsZi5fc3RhdGUgPT09IDApIHtcbiAgICBzZWxmLl9kZWZlcnJlZHMucHVzaChkZWZlcnJlZCk7XG4gICAgcmV0dXJuO1xuICB9XG4gIHNlbGYuX2hhbmRsZWQgPSB0cnVlO1xuICBQcm9taXNlLl9pbW1lZGlhdGVGbihmdW5jdGlvbigpIHtcbiAgICB2YXIgY2IgPSBzZWxmLl9zdGF0ZSA9PT0gMSA/IGRlZmVycmVkLm9uRnVsZmlsbGVkIDogZGVmZXJyZWQub25SZWplY3RlZDtcbiAgICBpZiAoY2IgPT09IG51bGwpIHtcbiAgICAgIChzZWxmLl9zdGF0ZSA9PT0gMSA/IHJlc29sdmUgOiByZWplY3QpKGRlZmVycmVkLnByb21pc2UsIHNlbGYuX3ZhbHVlKTtcbiAgICAgIHJldHVybjtcbiAgICB9XG4gICAgdmFyIHJldDtcbiAgICB0cnkge1xuICAgICAgcmV0ID0gY2Ioc2VsZi5fdmFsdWUpO1xuICAgIH0gY2F0Y2ggKGUpIHtcbiAgICAgIHJlamVjdChkZWZlcnJlZC5wcm9taXNlLCBlKTtcbiAgICAgIHJldHVybjtcbiAgICB9XG4gICAgcmVzb2x2ZShkZWZlcnJlZC5wcm9taXNlLCByZXQpO1xuICB9KTtcbn1cblxuZnVuY3Rpb24gcmVzb2x2ZShzZWxmLCBuZXdWYWx1ZSkge1xuICB0cnkge1xuICAgIC8vIFByb21pc2UgUmVzb2x1dGlvbiBQcm9jZWR1cmU6IGh0dHBzOi8vZ2l0aHViLmNvbS9wcm9taXNlcy1hcGx1cy9wcm9taXNlcy1zcGVjI3RoZS1wcm9taXNlLXJlc29sdXRpb24tcHJvY2VkdXJlXG4gICAgaWYgKG5ld1ZhbHVlID09PSBzZWxmKVxuICAgICAgdGhyb3cgbmV3IFR5cGVFcnJvcignQSBwcm9taXNlIGNhbm5vdCBiZSByZXNvbHZlZCB3aXRoIGl0c2VsZi4nKTtcbiAgICBpZiAoXG4gICAgICBuZXdWYWx1ZSAmJlxuICAgICAgKHR5cGVvZiBuZXdWYWx1ZSA9PT0gJ29iamVjdCcgfHwgdHlwZW9mIG5ld1ZhbHVlID09PSAnZnVuY3Rpb24nKVxuICAgICkge1xuICAgICAgdmFyIHRoZW4gPSBuZXdWYWx1ZS50aGVuO1xuICAgICAgaWYgKG5ld1ZhbHVlIGluc3RhbmNlb2YgUHJvbWlzZSkge1xuICAgICAgICBzZWxmLl9zdGF0ZSA9IDM7XG4gICAgICAgIHNlbGYuX3ZhbHVlID0gbmV3VmFsdWU7XG4gICAgICAgIGZpbmFsZShzZWxmKTtcbiAgICAgICAgcmV0dXJuO1xuICAgICAgfSBlbHNlIGlmICh0eXBlb2YgdGhlbiA9PT0gJ2Z1bmN0aW9uJykge1xuICAgICAgICBkb1Jlc29sdmUoYmluZCh0aGVuLCBuZXdWYWx1ZSksIHNlbGYpO1xuICAgICAgICByZXR1cm47XG4gICAgICB9XG4gICAgfVxuICAgIHNlbGYuX3N0YXRlID0gMTtcbiAgICBzZWxmLl92YWx1ZSA9IG5ld1ZhbHVlO1xuICAgIGZpbmFsZShzZWxmKTtcbiAgfSBjYXRjaCAoZSkge1xuICAgIHJlamVjdChzZWxmLCBlKTtcbiAgfVxufVxuXG5mdW5jdGlvbiByZWplY3Qoc2VsZiwgbmV3VmFsdWUpIHtcbiAgc2VsZi5fc3RhdGUgPSAyO1xuICBzZWxmLl92YWx1ZSA9IG5ld1ZhbHVlO1xuICBmaW5hbGUoc2VsZik7XG59XG5cbmZ1bmN0aW9uIGZpbmFsZShzZWxmKSB7XG4gIGlmIChzZWxmLl9zdGF0ZSA9PT0gMiAmJiBzZWxmLl9kZWZlcnJlZHMubGVuZ3RoID09PSAwKSB7XG4gICAgUHJvbWlzZS5faW1tZWRpYXRlRm4oZnVuY3Rpb24oKSB7XG4gICAgICBpZiAoIXNlbGYuX2hhbmRsZWQpIHtcbiAgICAgICAgUHJvbWlzZS5fdW5oYW5kbGVkUmVqZWN0aW9uRm4oc2VsZi5fdmFsdWUpO1xuICAgICAgfVxuICAgIH0pO1xuICB9XG5cbiAgZm9yICh2YXIgaSA9IDAsIGxlbiA9IHNlbGYuX2RlZmVycmVkcy5sZW5ndGg7IGkgPCBsZW47IGkrKykge1xuICAgIGhhbmRsZShzZWxmLCBzZWxmLl9kZWZlcnJlZHNbaV0pO1xuICB9XG4gIHNlbGYuX2RlZmVycmVkcyA9IG51bGw7XG59XG5cbi8qKlxuICogQGNvbnN0cnVjdG9yXG4gKi9cbmZ1bmN0aW9uIEhhbmRsZXIob25GdWxmaWxsZWQsIG9uUmVqZWN0ZWQsIHByb21pc2UpIHtcbiAgdGhpcy5vbkZ1bGZpbGxlZCA9IHR5cGVvZiBvbkZ1bGZpbGxlZCA9PT0gJ2Z1bmN0aW9uJyA/IG9uRnVsZmlsbGVkIDogbnVsbDtcbiAgdGhpcy5vblJlamVjdGVkID0gdHlwZW9mIG9uUmVqZWN0ZWQgPT09ICdmdW5jdGlvbicgPyBvblJlamVjdGVkIDogbnVsbDtcbiAgdGhpcy5wcm9taXNlID0gcHJvbWlzZTtcbn1cblxuLyoqXG4gKiBUYWtlIGEgcG90ZW50aWFsbHkgbWlzYmVoYXZpbmcgcmVzb2x2ZXIgZnVuY3Rpb24gYW5kIG1ha2Ugc3VyZVxuICogb25GdWxmaWxsZWQgYW5kIG9uUmVqZWN0ZWQgYXJlIG9ubHkgY2FsbGVkIG9uY2UuXG4gKlxuICogTWFrZXMgbm8gZ3VhcmFudGVlcyBhYm91dCBhc3luY2hyb255LlxuICovXG5mdW5jdGlvbiBkb1Jlc29sdmUoZm4sIHNlbGYpIHtcbiAgdmFyIGRvbmUgPSBmYWxzZTtcbiAgdHJ5IHtcbiAgICBmbihcbiAgICAgIGZ1bmN0aW9uKHZhbHVlKSB7XG4gICAgICAgIGlmIChkb25lKSByZXR1cm47XG4gICAgICAgIGRvbmUgPSB0cnVlO1xuICAgICAgICByZXNvbHZlKHNlbGYsIHZhbHVlKTtcbiAgICAgIH0sXG4gICAgICBmdW5jdGlvbihyZWFzb24pIHtcbiAgICAgICAgaWYgKGRvbmUpIHJldHVybjtcbiAgICAgICAgZG9uZSA9IHRydWU7XG4gICAgICAgIHJlamVjdChzZWxmLCByZWFzb24pO1xuICAgICAgfVxuICAgICk7XG4gIH0gY2F0Y2ggKGV4KSB7XG4gICAgaWYgKGRvbmUpIHJldHVybjtcbiAgICBkb25lID0gdHJ1ZTtcbiAgICByZWplY3Qoc2VsZiwgZXgpO1xuICB9XG59XG5cblByb21pc2UucHJvdG90eXBlWydjYXRjaCddID0gZnVuY3Rpb24ob25SZWplY3RlZCkge1xuICByZXR1cm4gdGhpcy50aGVuKG51bGwsIG9uUmVqZWN0ZWQpO1xufTtcblxuUHJvbWlzZS5wcm90b3R5cGUudGhlbiA9IGZ1bmN0aW9uKG9uRnVsZmlsbGVkLCBvblJlamVjdGVkKSB7XG4gIC8vIEB0cy1pZ25vcmVcbiAgdmFyIHByb20gPSBuZXcgdGhpcy5jb25zdHJ1Y3Rvcihub29wKTtcblxuICBoYW5kbGUodGhpcywgbmV3IEhhbmRsZXIob25GdWxmaWxsZWQsIG9uUmVqZWN0ZWQsIHByb20pKTtcbiAgcmV0dXJuIHByb207XG59O1xuXG5Qcm9taXNlLnByb3RvdHlwZVsnZmluYWxseSddID0gcHJvbWlzZUZpbmFsbHk7XG5cblByb21pc2UuYWxsID0gZnVuY3Rpb24oYXJyKSB7XG4gIHJldHVybiBuZXcgUHJvbWlzZShmdW5jdGlvbihyZXNvbHZlLCByZWplY3QpIHtcbiAgICBpZiAoIWlzQXJyYXkoYXJyKSkge1xuICAgICAgcmV0dXJuIHJlamVjdChuZXcgVHlwZUVycm9yKCdQcm9taXNlLmFsbCBhY2NlcHRzIGFuIGFycmF5JykpO1xuICAgIH1cblxuICAgIHZhciBhcmdzID0gQXJyYXkucHJvdG90eXBlLnNsaWNlLmNhbGwoYXJyKTtcbiAgICBpZiAoYXJncy5sZW5ndGggPT09IDApIHJldHVybiByZXNvbHZlKFtdKTtcbiAgICB2YXIgcmVtYWluaW5nID0gYXJncy5sZW5ndGg7XG5cbiAgICBmdW5jdGlvbiByZXMoaSwgdmFsKSB7XG4gICAgICB0cnkge1xuICAgICAgICBpZiAodmFsICYmICh0eXBlb2YgdmFsID09PSAnb2JqZWN0JyB8fCB0eXBlb2YgdmFsID09PSAnZnVuY3Rpb24nKSkge1xuICAgICAgICAgIHZhciB0aGVuID0gdmFsLnRoZW47XG4gICAgICAgICAgaWYgKHR5cGVvZiB0aGVuID09PSAnZnVuY3Rpb24nKSB7XG4gICAgICAgICAgICB0aGVuLmNhbGwoXG4gICAgICAgICAgICAgIHZhbCxcbiAgICAgICAgICAgICAgZnVuY3Rpb24odmFsKSB7XG4gICAgICAgICAgICAgICAgcmVzKGksIHZhbCk7XG4gICAgICAgICAgICAgIH0sXG4gICAgICAgICAgICAgIHJlamVjdFxuICAgICAgICAgICAgKTtcbiAgICAgICAgICAgIHJldHVybjtcbiAgICAgICAgICB9XG4gICAgICAgIH1cbiAgICAgICAgYXJnc1tpXSA9IHZhbDtcbiAgICAgICAgaWYgKC0tcmVtYWluaW5nID09PSAwKSB7XG4gICAgICAgICAgcmVzb2x2ZShhcmdzKTtcbiAgICAgICAgfVxuICAgICAgfSBjYXRjaCAoZXgpIHtcbiAgICAgICAgcmVqZWN0KGV4KTtcbiAgICAgIH1cbiAgICB9XG5cbiAgICBmb3IgKHZhciBpID0gMDsgaSA8IGFyZ3MubGVuZ3RoOyBpKyspIHtcbiAgICAgIHJlcyhpLCBhcmdzW2ldKTtcbiAgICB9XG4gIH0pO1xufTtcblxuUHJvbWlzZS5yZXNvbHZlID0gZnVuY3Rpb24odmFsdWUpIHtcbiAgaWYgKHZhbHVlICYmIHR5cGVvZiB2YWx1ZSA9PT0gJ29iamVjdCcgJiYgdmFsdWUuY29uc3RydWN0b3IgPT09IFByb21pc2UpIHtcbiAgICByZXR1cm4gdmFsdWU7XG4gIH1cblxuICByZXR1cm4gbmV3IFByb21pc2UoZnVuY3Rpb24ocmVzb2x2ZSkge1xuICAgIHJlc29sdmUodmFsdWUpO1xuICB9KTtcbn07XG5cblByb21pc2UucmVqZWN0ID0gZnVuY3Rpb24odmFsdWUpIHtcbiAgcmV0dXJuIG5ldyBQcm9taXNlKGZ1bmN0aW9uKHJlc29sdmUsIHJlamVjdCkge1xuICAgIHJlamVjdCh2YWx1ZSk7XG4gIH0pO1xufTtcblxuUHJvbWlzZS5yYWNlID0gZnVuY3Rpb24oYXJyKSB7XG4gIHJldHVybiBuZXcgUHJvbWlzZShmdW5jdGlvbihyZXNvbHZlLCByZWplY3QpIHtcbiAgICBpZiAoIWlzQXJyYXkoYXJyKSkge1xuICAgICAgcmV0dXJuIHJlamVjdChuZXcgVHlwZUVycm9yKCdQcm9taXNlLnJhY2UgYWNjZXB0cyBhbiBhcnJheScpKTtcbiAgICB9XG5cbiAgICBmb3IgKHZhciBpID0gMCwgbGVuID0gYXJyLmxlbmd0aDsgaSA8IGxlbjsgaSsrKSB7XG4gICAgICBQcm9taXNlLnJlc29sdmUoYXJyW2ldKS50aGVuKHJlc29sdmUsIHJlamVjdCk7XG4gICAgfVxuICB9KTtcbn07XG5cbi8vIFVzZSBwb2x5ZmlsbCBmb3Igc2V0SW1tZWRpYXRlIGZvciBwZXJmb3JtYW5jZSBnYWluc1xuUHJvbWlzZS5faW1tZWRpYXRlRm4gPVxuICAvLyBAdHMtaWdub3JlXG4gICh0eXBlb2Ygc2V0SW1tZWRpYXRlID09PSAnZnVuY3Rpb24nICYmXG4gICAgZnVuY3Rpb24oZm4pIHtcbiAgICAgIC8vIEB0cy1pZ25vcmVcbiAgICAgIHNldEltbWVkaWF0ZShmbik7XG4gICAgfSkgfHxcbiAgZnVuY3Rpb24oZm4pIHtcbiAgICBzZXRUaW1lb3V0RnVuYyhmbiwgMCk7XG4gIH07XG5cblByb21pc2UuX3VuaGFuZGxlZFJlamVjdGlvbkZuID0gZnVuY3Rpb24gX3VuaGFuZGxlZFJlamVjdGlvbkZuKGVycikge1xuICBpZiAodHlwZW9mIGNvbnNvbGUgIT09ICd1bmRlZmluZWQnICYmIGNvbnNvbGUpIHtcbiAgICBjb25zb2xlLndhcm4oJ1Bvc3NpYmxlIFVuaGFuZGxlZCBQcm9taXNlIFJlamVjdGlvbjonLCBlcnIpOyAvLyBlc2xpbnQtZGlzYWJsZS1saW5lIG5vLWNvbnNvbGVcbiAgfVxufTtcblxuZXhwb3J0IGRlZmF1bHQgUHJvbWlzZTtcbiIsIihmdW5jdGlvbiAocm9vdCwgZmFjdG9yeSkge1xuICAgICd1c2Ugc3RyaWN0JztcbiAgICAvLyBVbml2ZXJzYWwgTW9kdWxlIERlZmluaXRpb24gKFVNRCkgdG8gc3VwcG9ydCBBTUQsIENvbW1vbkpTL05vZGUuanMsIFJoaW5vLCBhbmQgYnJvd3NlcnMuXG5cbiAgICAvKiBpc3RhbmJ1bCBpZ25vcmUgbmV4dCAqL1xuICAgIGlmICh0eXBlb2YgZGVmaW5lID09PSAnZnVuY3Rpb24nICYmIGRlZmluZS5hbWQpIHtcbiAgICAgICAgZGVmaW5lKCdzdGFja2ZyYW1lJywgW10sIGZhY3RvcnkpO1xuICAgIH0gZWxzZSBpZiAodHlwZW9mIGV4cG9ydHMgPT09ICdvYmplY3QnKSB7XG4gICAgICAgIG1vZHVsZS5leHBvcnRzID0gZmFjdG9yeSgpO1xuICAgIH0gZWxzZSB7XG4gICAgICAgIHJvb3QuU3RhY2tGcmFtZSA9IGZhY3RvcnkoKTtcbiAgICB9XG59KHRoaXMsIGZ1bmN0aW9uICgpIHtcbiAgICAndXNlIHN0cmljdCc7XG4gICAgZnVuY3Rpb24gX2lzTnVtYmVyKG4pIHtcbiAgICAgICAgcmV0dXJuICFpc05hTihwYXJzZUZsb2F0KG4pKSAmJiBpc0Zpbml0ZShuKTtcbiAgICB9XG5cbiAgICBmdW5jdGlvbiBTdGFja0ZyYW1lKGZ1bmN0aW9uTmFtZSwgYXJncywgZmlsZU5hbWUsIGxpbmVOdW1iZXIsIGNvbHVtbk51bWJlciwgc291cmNlKSB7XG4gICAgICAgIGlmIChmdW5jdGlvbk5hbWUgIT09IHVuZGVmaW5lZCkge1xuICAgICAgICAgICAgdGhpcy5zZXRGdW5jdGlvbk5hbWUoZnVuY3Rpb25OYW1lKTtcbiAgICAgICAgfVxuICAgICAgICBpZiAoYXJncyAhPT0gdW5kZWZpbmVkKSB7XG4gICAgICAgICAgICB0aGlzLnNldEFyZ3MoYXJncyk7XG4gICAgICAgIH1cbiAgICAgICAgaWYgKGZpbGVOYW1lICE9PSB1bmRlZmluZWQpIHtcbiAgICAgICAgICAgIHRoaXMuc2V0RmlsZU5hbWUoZmlsZU5hbWUpO1xuICAgICAgICB9XG4gICAgICAgIGlmIChsaW5lTnVtYmVyICE9PSB1bmRlZmluZWQpIHtcbiAgICAgICAgICAgIHRoaXMuc2V0TGluZU51bWJlcihsaW5lTnVtYmVyKTtcbiAgICAgICAgfVxuICAgICAgICBpZiAoY29sdW1uTnVtYmVyICE9PSB1bmRlZmluZWQpIHtcbiAgICAgICAgICAgIHRoaXMuc2V0Q29sdW1uTnVtYmVyKGNvbHVtbk51bWJlcik7XG4gICAgICAgIH1cbiAgICAgICAgaWYgKHNvdXJjZSAhPT0gdW5kZWZpbmVkKSB7XG4gICAgICAgICAgICB0aGlzLnNldFNvdXJjZShzb3VyY2UpO1xuICAgICAgICB9XG4gICAgfVxuXG4gICAgU3RhY2tGcmFtZS5wcm90b3R5cGUgPSB7XG4gICAgICAgIGdldEZ1bmN0aW9uTmFtZTogZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgcmV0dXJuIHRoaXMuZnVuY3Rpb25OYW1lO1xuICAgICAgICB9LFxuICAgICAgICBzZXRGdW5jdGlvbk5hbWU6IGZ1bmN0aW9uICh2KSB7XG4gICAgICAgICAgICB0aGlzLmZ1bmN0aW9uTmFtZSA9IFN0cmluZyh2KTtcbiAgICAgICAgfSxcblxuICAgICAgICBnZXRBcmdzOiBmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICByZXR1cm4gdGhpcy5hcmdzO1xuICAgICAgICB9LFxuICAgICAgICBzZXRBcmdzOiBmdW5jdGlvbiAodikge1xuICAgICAgICAgICAgaWYgKE9iamVjdC5wcm90b3R5cGUudG9TdHJpbmcuY2FsbCh2KSAhPT0gJ1tvYmplY3QgQXJyYXldJykge1xuICAgICAgICAgICAgICAgIHRocm93IG5ldyBUeXBlRXJyb3IoJ0FyZ3MgbXVzdCBiZSBhbiBBcnJheScpO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgdGhpcy5hcmdzID0gdjtcbiAgICAgICAgfSxcblxuICAgICAgICAvLyBOT1RFOiBQcm9wZXJ0eSBuYW1lIG1heSBiZSBtaXNsZWFkaW5nIGFzIGl0IGluY2x1ZGVzIHRoZSBwYXRoLFxuICAgICAgICAvLyBidXQgaXQgc29tZXdoYXQgbWlycm9ycyBWOCdzIEphdmFTY3JpcHRTdGFja1RyYWNlQXBpXG4gICAgICAgIC8vIGh0dHBzOi8vY29kZS5nb29nbGUuY29tL3Avdjgvd2lraS9KYXZhU2NyaXB0U3RhY2tUcmFjZUFwaSBhbmQgR2Vja28nc1xuICAgICAgICAvLyBodHRwOi8vbXhyLm1vemlsbGEub3JnL21vemlsbGEtY2VudHJhbC9zb3VyY2UveHBjb20vYmFzZS9uc0lFeGNlcHRpb24uaWRsIzE0XG4gICAgICAgIGdldEZpbGVOYW1lOiBmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgICByZXR1cm4gdGhpcy5maWxlTmFtZTtcbiAgICAgICAgfSxcbiAgICAgICAgc2V0RmlsZU5hbWU6IGZ1bmN0aW9uICh2KSB7XG4gICAgICAgICAgICB0aGlzLmZpbGVOYW1lID0gU3RyaW5nKHYpO1xuICAgICAgICB9LFxuXG4gICAgICAgIGdldExpbmVOdW1iZXI6IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIHJldHVybiB0aGlzLmxpbmVOdW1iZXI7XG4gICAgICAgIH0sXG4gICAgICAgIHNldExpbmVOdW1iZXI6IGZ1bmN0aW9uICh2KSB7XG4gICAgICAgICAgICBpZiAoIV9pc051bWJlcih2KSkge1xuICAgICAgICAgICAgICAgIHRocm93IG5ldyBUeXBlRXJyb3IoJ0xpbmUgTnVtYmVyIG11c3QgYmUgYSBOdW1iZXInKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIHRoaXMubGluZU51bWJlciA9IE51bWJlcih2KTtcbiAgICAgICAgfSxcblxuICAgICAgICBnZXRDb2x1bW5OdW1iZXI6IGZ1bmN0aW9uICgpIHtcbiAgICAgICAgICAgIHJldHVybiB0aGlzLmNvbHVtbk51bWJlcjtcbiAgICAgICAgfSxcbiAgICAgICAgc2V0Q29sdW1uTnVtYmVyOiBmdW5jdGlvbiAodikge1xuICAgICAgICAgICAgaWYgKCFfaXNOdW1iZXIodikpIHtcbiAgICAgICAgICAgICAgICB0aHJvdyBuZXcgVHlwZUVycm9yKCdDb2x1bW4gTnVtYmVyIG11c3QgYmUgYSBOdW1iZXInKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICAgIHRoaXMuY29sdW1uTnVtYmVyID0gTnVtYmVyKHYpO1xuICAgICAgICB9LFxuXG4gICAgICAgIGdldFNvdXJjZTogZnVuY3Rpb24gKCkge1xuICAgICAgICAgICAgcmV0dXJuIHRoaXMuc291cmNlO1xuICAgICAgICB9LFxuICAgICAgICBzZXRTb3VyY2U6IGZ1bmN0aW9uICh2KSB7XG4gICAgICAgICAgICB0aGlzLnNvdXJjZSA9IFN0cmluZyh2KTtcbiAgICAgICAgfSxcblxuICAgICAgICB0b1N0cmluZzogZnVuY3Rpb24oKSB7XG4gICAgICAgICAgICB2YXIgZnVuY3Rpb25OYW1lID0gdGhpcy5nZXRGdW5jdGlvbk5hbWUoKSB8fCAne2Fub255bW91c30nO1xuICAgICAgICAgICAgdmFyIGFyZ3MgPSAnKCcgKyAodGhpcy5nZXRBcmdzKCkgfHwgW10pLmpvaW4oJywnKSArICcpJztcbiAgICAgICAgICAgIHZhciBmaWxlTmFtZSA9IHRoaXMuZ2V0RmlsZU5hbWUoKSA/ICgnQCcgKyB0aGlzLmdldEZpbGVOYW1lKCkpIDogJyc7XG4gICAgICAgICAgICB2YXIgbGluZU51bWJlciA9IF9pc051bWJlcih0aGlzLmdldExpbmVOdW1iZXIoKSkgPyAoJzonICsgdGhpcy5nZXRMaW5lTnVtYmVyKCkpIDogJyc7XG4gICAgICAgICAgICB2YXIgY29sdW1uTnVtYmVyID0gX2lzTnVtYmVyKHRoaXMuZ2V0Q29sdW1uTnVtYmVyKCkpID8gKCc6JyArIHRoaXMuZ2V0Q29sdW1uTnVtYmVyKCkpIDogJyc7XG4gICAgICAgICAgICByZXR1cm4gZnVuY3Rpb25OYW1lICsgYXJncyArIGZpbGVOYW1lICsgbGluZU51bWJlciArIGNvbHVtbk51bWJlcjtcbiAgICAgICAgfVxuICAgIH07XG5cbiAgICByZXR1cm4gU3RhY2tGcmFtZTtcbn0pKTtcbiIsIi8vIFRoZSBtb2R1bGUgY2FjaGVcbnZhciBfX3dlYnBhY2tfbW9kdWxlX2NhY2hlX18gPSB7fTtcblxuLy8gVGhlIHJlcXVpcmUgZnVuY3Rpb25cbmZ1bmN0aW9uIF9fd2VicGFja19yZXF1aXJlX18obW9kdWxlSWQpIHtcblx0Ly8gQ2hlY2sgaWYgbW9kdWxlIGlzIGluIGNhY2hlXG5cdHZhciBjYWNoZWRNb2R1bGUgPSBfX3dlYnBhY2tfbW9kdWxlX2NhY2hlX19bbW9kdWxlSWRdO1xuXHRpZiAoY2FjaGVkTW9kdWxlICE9PSB1bmRlZmluZWQpIHtcblx0XHRyZXR1cm4gY2FjaGVkTW9kdWxlLmV4cG9ydHM7XG5cdH1cblx0Ly8gQ3JlYXRlIGEgbmV3IG1vZHVsZSAoYW5kIHB1dCBpdCBpbnRvIHRoZSBjYWNoZSlcblx0dmFyIG1vZHVsZSA9IF9fd2VicGFja19tb2R1bGVfY2FjaGVfX1ttb2R1bGVJZF0gPSB7XG5cdFx0Ly8gbm8gbW9kdWxlLmlkIG5lZWRlZFxuXHRcdC8vIG5vIG1vZHVsZS5sb2FkZWQgbmVlZGVkXG5cdFx0ZXhwb3J0czoge31cblx0fTtcblxuXHQvLyBFeGVjdXRlIHRoZSBtb2R1bGUgZnVuY3Rpb25cblx0X193ZWJwYWNrX21vZHVsZXNfX1ttb2R1bGVJZF0uY2FsbChtb2R1bGUuZXhwb3J0cywgbW9kdWxlLCBtb2R1bGUuZXhwb3J0cywgX193ZWJwYWNrX3JlcXVpcmVfXyk7XG5cblx0Ly8gUmV0dXJuIHRoZSBleHBvcnRzIG9mIHRoZSBtb2R1bGVcblx0cmV0dXJuIG1vZHVsZS5leHBvcnRzO1xufVxuXG4iLCIvLyBnZXREZWZhdWx0RXhwb3J0IGZ1bmN0aW9uIGZvciBjb21wYXRpYmlsaXR5IHdpdGggbm9uLWhhcm1vbnkgbW9kdWxlc1xuX193ZWJwYWNrX3JlcXVpcmVfXy5uID0gZnVuY3Rpb24obW9kdWxlKSB7XG5cdHZhciBnZXR0ZXIgPSBtb2R1bGUgJiYgbW9kdWxlLl9fZXNNb2R1bGUgP1xuXHRcdGZ1bmN0aW9uKCkgeyByZXR1cm4gbW9kdWxlWydkZWZhdWx0J107IH0gOlxuXHRcdGZ1bmN0aW9uKCkgeyByZXR1cm4gbW9kdWxlOyB9O1xuXHRfX3dlYnBhY2tfcmVxdWlyZV9fLmQoZ2V0dGVyLCB7IGE6IGdldHRlciB9KTtcblx0cmV0dXJuIGdldHRlcjtcbn07IiwiLy8gZGVmaW5lIGdldHRlciBmdW5jdGlvbnMgZm9yIGhhcm1vbnkgZXhwb3J0c1xuX193ZWJwYWNrX3JlcXVpcmVfXy5kID0gZnVuY3Rpb24oZXhwb3J0cywgZGVmaW5pdGlvbikge1xuXHRmb3IodmFyIGtleSBpbiBkZWZpbml0aW9uKSB7XG5cdFx0aWYoX193ZWJwYWNrX3JlcXVpcmVfXy5vKGRlZmluaXRpb24sIGtleSkgJiYgIV9fd2VicGFja19yZXF1aXJlX18ubyhleHBvcnRzLCBrZXkpKSB7XG5cdFx0XHRPYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywga2V5LCB7IGVudW1lcmFibGU6IHRydWUsIGdldDogZGVmaW5pdGlvbltrZXldIH0pO1xuXHRcdH1cblx0fVxufTsiLCJfX3dlYnBhY2tfcmVxdWlyZV9fLm8gPSBmdW5jdGlvbihvYmosIHByb3ApIHsgcmV0dXJuIE9iamVjdC5wcm90b3R5cGUuaGFzT3duUHJvcGVydHkuY2FsbChvYmosIHByb3ApOyB9IiwiLy8gZGVmaW5lIF9fZXNNb2R1bGUgb24gZXhwb3J0c1xuX193ZWJwYWNrX3JlcXVpcmVfXy5yID0gZnVuY3Rpb24oZXhwb3J0cykge1xuXHRpZih0eXBlb2YgU3ltYm9sICE9PSAndW5kZWZpbmVkJyAmJiBTeW1ib2wudG9TdHJpbmdUYWcpIHtcblx0XHRPYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgU3ltYm9sLnRvU3RyaW5nVGFnLCB7IHZhbHVlOiAnTW9kdWxlJyB9KTtcblx0fVxuXHRPYmplY3QuZGVmaW5lUHJvcGVydHkoZXhwb3J0cywgJ19fZXNNb2R1bGUnLCB7IHZhbHVlOiB0cnVlIH0pO1xufTsiLCIvKipcbiAqIE1JVCBMaWNlbnNlXG4gKlxuICogQ29weXJpZ2h0IChjKSAyMDE3LXByZXNlbnQsIEVsYXN0aWNzZWFyY2ggQlZcbiAqXG4gKiBQZXJtaXNzaW9uIGlzIGhlcmVieSBncmFudGVkLCBmcmVlIG9mIGNoYXJnZSwgdG8gYW55IHBlcnNvbiBvYnRhaW5pbmcgYSBjb3B5XG4gKiBvZiB0aGlzIHNvZnR3YXJlIGFuZCBhc3NvY2lhdGVkIGRvY3VtZW50YXRpb24gZmlsZXMgKHRoZSBcIlNvZnR3YXJlXCIpLCB0byBkZWFsXG4gKiBpbiB0aGUgU29mdHdhcmUgd2l0aG91dCByZXN0cmljdGlvbiwgaW5jbHVkaW5nIHdpdGhvdXQgbGltaXRhdGlvbiB0aGUgcmlnaHRzXG4gKiB0byB1c2UsIGNvcHksIG1vZGlmeSwgbWVyZ2UsIHB1Ymxpc2gsIGRpc3RyaWJ1dGUsIHN1YmxpY2Vuc2UsIGFuZC9vciBzZWxsXG4gKiBjb3BpZXMgb2YgdGhlIFNvZnR3YXJlLCBhbmQgdG8gcGVybWl0IHBlcnNvbnMgdG8gd2hvbSB0aGUgU29mdHdhcmUgaXNcbiAqIGZ1cm5pc2hlZCB0byBkbyBzbywgc3ViamVjdCB0byB0aGUgZm9sbG93aW5nIGNvbmRpdGlvbnM6XG4gKlxuICogVGhlIGFib3ZlIGNvcHlyaWdodCBub3RpY2UgYW5kIHRoaXMgcGVybWlzc2lvbiBub3RpY2Ugc2hhbGwgYmUgaW5jbHVkZWQgaW5cbiAqIGFsbCBjb3BpZXMgb3Igc3Vic3RhbnRpYWwgcG9ydGlvbnMgb2YgdGhlIFNvZnR3YXJlLlxuICpcbiAqIFRIRSBTT0ZUV0FSRSBJUyBQUk9WSURFRCBcIkFTIElTXCIsIFdJVEhPVVQgV0FSUkFOVFkgT0YgQU5ZIEtJTkQsIEVYUFJFU1MgT1JcbiAqIElNUExJRUQsIElOQ0xVRElORyBCVVQgTk9UIExJTUlURUQgVE8gVEhFIFdBUlJBTlRJRVMgT0YgTUVSQ0hBTlRBQklMSVRZLFxuICogRklUTkVTUyBGT1IgQSBQQVJUSUNVTEFSIFBVUlBPU0UgQU5EIE5PTklORlJJTkdFTUVOVC4gSU4gTk8gRVZFTlQgU0hBTEwgVEhFXG4gKiBBVVRIT1JTIE9SIENPUFlSSUdIVCBIT0xERVJTIEJFIExJQUJMRSBGT1IgQU5ZIENMQUlNLCBEQU1BR0VTIE9SIE9USEVSXG4gKiBMSUFCSUxJVFksIFdIRVRIRVIgSU4gQU4gQUNUSU9OIE9GIENPTlRSQUNULCBUT1JUIE9SIE9USEVSV0lTRSwgQVJJU0lORyBGUk9NLFxuICogT1VUIE9GIE9SIElOIENPTk5FQ1RJT04gV0lUSCBUSEUgU09GVFdBUkUgT1IgVEhFIFVTRSBPUiBPVEhFUiBERUFMSU5HUyBJTlxuICogVEhFIFNPRlRXQVJFLlxuICpcbiAqL1xuXG5pbXBvcnQge1xuICBjcmVhdGVTZXJ2aWNlRmFjdG9yeSxcbiAgYm9vdHN0cmFwLFxuICBpc0Jyb3dzZXJcbn0gZnJvbSAnQGVsYXN0aWMvYXBtLXJ1bS1jb3JlJ1xuaW1wb3J0IEFwbUJhc2UgZnJvbSAnLi9hcG0tYmFzZSdcblxuLyoqXG4gKiBVc2UgYSBzaW5nbGUgaW5zdGFuY2Ugb2YgQXBtQmFzZSBhY3Jvc3MgYWxsIGluc3RhbmNlIG9mIHRoZSBhZ2VudFxuICogaW5jbHVkaW5nIHRoZSBpbnN0YW5jZXMgdXNlZCBpbiBmcmFtZXdvcmsgc3BlY2lmaWMgaW50ZWdyYXRpb25zXG4gKi9cbmZ1bmN0aW9uIGdldEFwbUJhc2UoKSB7XG4gIGlmIChpc0Jyb3dzZXIgJiYgd2luZG93LmVsYXN0aWNBcG0pIHtcbiAgICByZXR1cm4gd2luZG93LmVsYXN0aWNBcG1cbiAgfVxuICBjb25zdCBlbmFibGVkID0gYm9vdHN0cmFwKClcbiAgY29uc3Qgc2VydmljZUZhY3RvcnkgPSBjcmVhdGVTZXJ2aWNlRmFjdG9yeSgpXG4gIGNvbnN0IGFwbUJhc2UgPSBuZXcgQXBtQmFzZShzZXJ2aWNlRmFjdG9yeSwgIWVuYWJsZWQpXG5cbiAgaWYgKGlzQnJvd3Nlcikge1xuICAgIHdpbmRvdy5lbGFzdGljQXBtID0gYXBtQmFzZVxuICB9XG5cbiAgcmV0dXJuIGFwbUJhc2Vcbn1cblxuY29uc3QgYXBtQmFzZSA9IGdldEFwbUJhc2UoKVxuXG5jb25zdCBpbml0ID0gYXBtQmFzZS5pbml0LmJpbmQoYXBtQmFzZSlcblxuZXhwb3J0IGRlZmF1bHQgaW5pdFxuZXhwb3J0IHsgaW5pdCwgYXBtQmFzZSwgQXBtQmFzZSwgYXBtQmFzZSBhcyBhcG0gfVxuIl0sIm1hcHBpbmdzIjoiQUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOzs7Ozs7Ozs7Ozs7Ozs7OztBQ1ZBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7OztBQ2RBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0E7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQ1ZBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBQ0E7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBQ0E7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUtBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUNBO0FBTUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBTEE7QUFPQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUxBO0FBT0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBTEE7QUFPQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFJQTtBQUFBO0FBQ0E7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFEQTtBQUdBO0FBVkE7QUFZQTtBQWJBO0FBZUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUNwV0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBTEE7QUFPQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFLQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUNBO0FBTUE7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUtBO0FBQ0E7QUFQQTtBQVNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFLQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUhBO0FBS0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFFQTtBQUFBO0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFEQTtBQUdBO0FBVkE7QUFZQTtBQWJBO0FBZUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBUkE7QUFDQTtBQVVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBZkE7QUFDQTtBQWlCQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFLQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSkE7QUFNQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFHQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFLQTtBQVJBO0FBVUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBREE7QUFHQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFEQTtBQUpBO0FBSkE7QUFhQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFEQTtBQVBBO0FBREE7QUFhQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUhBO0FBS0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7O0FDNVZBO0FBQUE7QUFBQTtBQUFBO0FBQ0E7QUFEQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQURBO0FBQUE7QUFDQTtBQURBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBOUJBO0FBZ0NBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQ0E7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQ0E7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUtBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUhBO0FBS0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFLQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0E7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUM3UUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7OztBOzs7Ozs7Ozs7Ozs7Ozs7Ozs7QUN0REE7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQURBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQURBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUtBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFLQTtBQUNBO0FBUEE7QUFTQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFJQTtBQUxBO0FBT0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBTEE7QUFPQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFEQTtBQU1BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQVhBO0FBQ0E7QUFhQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7QUNyS0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0E7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQ25EQTtBQUFBO0FBQUE7QUFBQTtBQUNBO0FBREE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQ0E7QUFEQTtBQUFBO0FBQ0E7QUFEQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQU9BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFMQTtBQU9BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFDQTtBQUtBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7O0FDM0VBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7Ozs7O0FDTkE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFNQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUtBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUtBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFMQTtBQU9BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUhBO0FBS0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7OztBQzFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7OztBQ2hCQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0E7Ozs7Ozs7Ozs7QUMzREE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7Ozs7QUNWQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQ0E7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUhBO0FBQ0E7QUFLQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQURBO0FBS0E7QUFDQTtBQUNBO0FBQ0E7O0E7Ozs7Ozs7Ozs7Ozs7Ozs7QUM5REE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7Ozs7Ozs7QUN6Q0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSkE7QUFKQTtBQVdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7Ozs7QUNuSEE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUZBO0FBUUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQ3RCQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7O0E7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUN4QkE7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0E7Ozs7Ozs7Ozs7Ozs7OztBQ3pEQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFMQTtBQUpBO0FBQ0E7QUFZQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7Ozs7O0FDN0ZBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7OztBOzs7Ozs7Ozs7O0FDVkE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FDckRBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUFBO0FBQUE7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7O0E7Ozs7Ozs7Ozs7Ozs7QUN2RUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUN0QkE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBTkE7QUFRQTtBQUNBO0FBREE7QUFUQTtBQWFBO0FBQ0E7QUFDQTtBQUNBO0FBREE7QUFGQTtBQU1BO0FBQ0E7QUFDQTtBQUNBO0FBREE7QUFGQTtBQU1BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUtBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFiQTtBQWVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBVEE7QUFXQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBREE7QUFHQTtBQVRBO0FBV0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQURBO0FBR0E7QUFaQTtBQUNBO0FBY0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOzs7QTs7Ozs7Ozs7Ozs7Ozs7O0FDeEpBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUxBO0FBQ0E7QUFPQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQ0E7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUtBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQ2xNQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFLQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7OztBOzs7Ozs7Ozs7Ozs7Ozs7O0FDN1dBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQ0E7QUFEQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQ0E7QUFEQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQ0E7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQUtBO0FBUkE7QUFDQTtBQVVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUpBO0FBU0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7Ozs7O0FDdExBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQ0E7QUFJQTtBQUNBO0FBQ0E7QUFDQTs7O0E7Ozs7Ozs7Ozs7Ozs7O0FDZEE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFBQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFLQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQUtBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUxBO0FBT0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBRUE7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FDdElBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOzs7QTs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FDbEJBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7O0E7Ozs7Ozs7Ozs7Ozs7QUNYQTtBQUFBO0FBQUE7QUFDQTtBQURBO0FBQUE7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQURBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUhBO0FBS0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFEQTtBQU9BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7Ozs7O0FDM0ZBO0FBQUE7QUFBQTtBQUNBO0FBREE7QUFBQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUNBO0FBREE7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBQ0E7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQVhBO0FBYUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQVhBO0FBQ0E7QUFhQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7Ozs7QUMzSEE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFBQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBSEE7QUFRQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFHQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUhBO0FBRkE7QUFDQTtBQVFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFKQTtBQU1BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQ0E7QUFHQTtBQUFBO0FBQUE7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBSUE7QUFDQTtBQU5BO0FBUUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUN6S0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQ0E7QUFLQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFGQTtBQVFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOzs7QTs7Ozs7Ozs7Ozs7Ozs7Ozs7QUM5TUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUNBO0FBS0E7QUFDQTtBQUNBO0FBQ0E7OztBOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQ3hCQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFKQTtBQU1BO0FBQ0E7QUFDQTtBQUNBO0FBSEE7QUFiQTtBQW1CQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUtBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFLQTtBQUNBO0FBQ0E7QUFGQTtBQUNBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFFQTtBQUNBO0FBREE7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUVBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBQ0E7QUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFDQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FDOU1BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUNBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFkQTtBQWdCQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBakJBO0FBbUJBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7O0E7Ozs7Ozs7Ozs7OztBQzlWQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7O0FDdkZBO0FBQUE7QUFBQTtBQUNBO0FBREE7QUFBQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUNBO0FBREE7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7Ozs7Ozs7Ozs7OztBQ3pDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFBQTtBQUFBO0FBQ0E7QUFNQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFKQTtBQU1BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFBQTtBQUNBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUhBO0FBS0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBSUE7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFIQTtBQURBO0FBQ0E7QUFPQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFGQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7Ozs7QUNoWkE7QUFBQTtBQUFBO0FBQ0E7QUFEQTtBQUFBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQ0E7QUFEQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBREE7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBOzs7Ozs7Ozs7Ozs7OztBQzFLQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7OztBOzs7Ozs7Ozs7Ozs7Ozs7OztBQ3VCQTtBQUNBO0FBZ0JBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOzs7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUNBO0FBV0E7QUFDQTtBQUlBO0FBQ0E7QUFJQTtBQUNBO0FBQUE7QUFDQTtBQUVBO0FBS0E7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQ0E7QUFFQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBTUE7QUFDQTtBQUFBO0FBQUE7QUFBQTtBQUNBO0FBU0E7QUFNQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBS0E7QUFDQTtBQUNBO0FBRkE7QUFDQTtBQUlBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBT0E7QUFBQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQWdCQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBR0E7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQUFBO0FBQ0E7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUFBO0FBQUE7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUFBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQURBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBR0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7Ozs7O0E7Ozs7Ozs7O0FDdlVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQ0EsYUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOzs7QTs7Ozs7Ozs7O0FDeE5BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7O0FDOURBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7O0FDbkNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0E7Ozs7Ozs7OztBQ2hCQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7O0FDMUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QTs7Ozs7Ozs7O0FDOU1BO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0E7Ozs7Ozs7OztBQ25CQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0E7Ozs7Ozs7Ozs7QUNsSkE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7O0E7Ozs7Ozs7Ozs7O0FDdEJBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7O0E7Ozs7Ozs7O0FDM1BBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUFBO0FBQ0EsYUFJQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7OztBOzs7O0FDMUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7OztBQ3ZCQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOzs7OztBQ1BBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7Ozs7O0FDUEE7Ozs7O0FDQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUNtQkE7QUFLQTtBQUNBO0FBS0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUVBO0FBRUE7Ozs7OztBIiwic291cmNlUm9vdCI6IiJ9