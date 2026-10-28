"use strict";
var __defProp = Object.defineProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};

// scripts/validate-survey.mjs
var import_node_fs = require("node:fs");

// node_modules/zod/v3/external.js
var external_exports = {};
__export(external_exports, {
  BRAND: () => BRAND,
  DIRTY: () => DIRTY,
  EMPTY_PATH: () => EMPTY_PATH,
  INVALID: () => INVALID,
  NEVER: () => NEVER,
  OK: () => OK,
  ParseStatus: () => ParseStatus,
  Schema: () => ZodType,
  ZodAny: () => ZodAny,
  ZodArray: () => ZodArray,
  ZodBigInt: () => ZodBigInt,
  ZodBoolean: () => ZodBoolean,
  ZodBranded: () => ZodBranded,
  ZodCatch: () => ZodCatch,
  ZodDate: () => ZodDate,
  ZodDefault: () => ZodDefault,
  ZodDiscriminatedUnion: () => ZodDiscriminatedUnion,
  ZodEffects: () => ZodEffects,
  ZodEnum: () => ZodEnum,
  ZodError: () => ZodError,
  ZodFirstPartyTypeKind: () => ZodFirstPartyTypeKind,
  ZodFunction: () => ZodFunction,
  ZodIntersection: () => ZodIntersection,
  ZodIssueCode: () => ZodIssueCode,
  ZodLazy: () => ZodLazy,
  ZodLiteral: () => ZodLiteral,
  ZodMap: () => ZodMap,
  ZodNaN: () => ZodNaN,
  ZodNativeEnum: () => ZodNativeEnum,
  ZodNever: () => ZodNever,
  ZodNull: () => ZodNull,
  ZodNullable: () => ZodNullable,
  ZodNumber: () => ZodNumber,
  ZodObject: () => ZodObject,
  ZodOptional: () => ZodOptional,
  ZodParsedType: () => ZodParsedType,
  ZodPipeline: () => ZodPipeline,
  ZodPromise: () => ZodPromise,
  ZodReadonly: () => ZodReadonly,
  ZodRecord: () => ZodRecord,
  ZodSchema: () => ZodType,
  ZodSet: () => ZodSet,
  ZodString: () => ZodString,
  ZodSymbol: () => ZodSymbol,
  ZodTransformer: () => ZodEffects,
  ZodTuple: () => ZodTuple,
  ZodType: () => ZodType,
  ZodUndefined: () => ZodUndefined,
  ZodUnion: () => ZodUnion,
  ZodUnknown: () => ZodUnknown,
  ZodVoid: () => ZodVoid,
  addIssueToContext: () => addIssueToContext,
  any: () => anyType,
  array: () => arrayType,
  bigint: () => bigIntType,
  boolean: () => booleanType,
  coerce: () => coerce,
  custom: () => custom,
  date: () => dateType,
  datetimeRegex: () => datetimeRegex,
  defaultErrorMap: () => en_default,
  discriminatedUnion: () => discriminatedUnionType,
  effect: () => effectsType,
  enum: () => enumType,
  function: () => functionType,
  getErrorMap: () => getErrorMap,
  getParsedType: () => getParsedType,
  instanceof: () => instanceOfType,
  intersection: () => intersectionType,
  isAborted: () => isAborted,
  isAsync: () => isAsync,
  isDirty: () => isDirty,
  isValid: () => isValid,
  late: () => late,
  lazy: () => lazyType,
  literal: () => literalType,
  makeIssue: () => makeIssue,
  map: () => mapType,
  nan: () => nanType,
  nativeEnum: () => nativeEnumType,
  never: () => neverType,
  null: () => nullType,
  nullable: () => nullableType,
  number: () => numberType,
  object: () => objectType,
  objectUtil: () => objectUtil,
  oboolean: () => oboolean,
  onumber: () => onumber,
  optional: () => optionalType,
  ostring: () => ostring,
  pipeline: () => pipelineType,
  preprocess: () => preprocessType,
  promise: () => promiseType,
  quotelessJson: () => quotelessJson,
  record: () => recordType,
  set: () => setType,
  setErrorMap: () => setErrorMap,
  strictObject: () => strictObjectType,
  string: () => stringType,
  symbol: () => symbolType,
  transformer: () => effectsType,
  tuple: () => tupleType,
  undefined: () => undefinedType,
  union: () => unionType,
  unknown: () => unknownType,
  util: () => util,
  void: () => voidType
});

// node_modules/zod/v3/helpers/util.js
var util;
(function(util2) {
  util2.assertEqual = (_) => {
  };
  function assertIs(_arg) {
  }
  util2.assertIs = assertIs;
  function assertNever(_x) {
    throw new Error();
  }
  util2.assertNever = assertNever;
  util2.arrayToEnum = (items) => {
    const obj = {};
    for (const item of items) {
      obj[item] = item;
    }
    return obj;
  };
  util2.getValidEnumValues = (obj) => {
    const validKeys = util2.objectKeys(obj).filter((k) => typeof obj[obj[k]] !== "number");
    const filtered = {};
    for (const k of validKeys) {
      filtered[k] = obj[k];
    }
    return util2.objectValues(filtered);
  };
  util2.objectValues = (obj) => {
    return util2.objectKeys(obj).map(function(e) {
      return obj[e];
    });
  };
  util2.objectKeys = typeof Object.keys === "function" ? (obj) => Object.keys(obj) : (object) => {
    const keys = [];
    for (const key in object) {
      if (Object.prototype.hasOwnProperty.call(object, key)) {
        keys.push(key);
      }
    }
    return keys;
  };
  util2.find = (arr, checker) => {
    for (const item of arr) {
      if (checker(item))
        return item;
    }
    return void 0;
  };
  util2.isInteger = typeof Number.isInteger === "function" ? (val) => Number.isInteger(val) : (val) => typeof val === "number" && Number.isFinite(val) && Math.floor(val) === val;
  function joinValues(array, separator = " | ") {
    return array.map((val) => typeof val === "string" ? `'${val}'` : val).join(separator);
  }
  util2.joinValues = joinValues;
  util2.jsonStringifyReplacer = (_, value) => {
    if (typeof value === "bigint") {
      return value.toString();
    }
    return value;
  };
})(util || (util = {}));
var objectUtil;
(function(objectUtil2) {
  objectUtil2.mergeShapes = (first, second) => {
    return {
      ...first,
      ...second
      // second overwrites first
    };
  };
})(objectUtil || (objectUtil = {}));
var ZodParsedType = util.arrayToEnum([
  "string",
  "nan",
  "number",
  "integer",
  "float",
  "boolean",
  "date",
  "bigint",
  "symbol",
  "function",
  "undefined",
  "null",
  "array",
  "object",
  "unknown",
  "promise",
  "void",
  "never",
  "map",
  "set"
]);
var getParsedType = (data) => {
  const t = typeof data;
  switch (t) {
    case "undefined":
      return ZodParsedType.undefined;
    case "string":
      return ZodParsedType.string;
    case "number":
      return Number.isNaN(data) ? ZodParsedType.nan : ZodParsedType.number;
    case "boolean":
      return ZodParsedType.boolean;
    case "function":
      return ZodParsedType.function;
    case "bigint":
      return ZodParsedType.bigint;
    case "symbol":
      return ZodParsedType.symbol;
    case "object":
      if (Array.isArray(data)) {
        return ZodParsedType.array;
      }
      if (data === null) {
        return ZodParsedType.null;
      }
      if (data.then && typeof data.then === "function" && data.catch && typeof data.catch === "function") {
        return ZodParsedType.promise;
      }
      if (typeof Map !== "undefined" && data instanceof Map) {
        return ZodParsedType.map;
      }
      if (typeof Set !== "undefined" && data instanceof Set) {
        return ZodParsedType.set;
      }
      if (typeof Date !== "undefined" && data instanceof Date) {
        return ZodParsedType.date;
      }
      return ZodParsedType.object;
    default:
      return ZodParsedType.unknown;
  }
};

// node_modules/zod/v3/ZodError.js
var ZodIssueCode = util.arrayToEnum([
  "invalid_type",
  "invalid_literal",
  "custom",
  "invalid_union",
  "invalid_union_discriminator",
  "invalid_enum_value",
  "unrecognized_keys",
  "invalid_arguments",
  "invalid_return_type",
  "invalid_date",
  "invalid_string",
  "too_small",
  "too_big",
  "invalid_intersection_types",
  "not_multiple_of",
  "not_finite"
]);
var quotelessJson = (obj) => {
  const json = JSON.stringify(obj, null, 2);
  return json.replace(/"([^"]+)":/g, "$1:");
};
var ZodError = class _ZodError extends Error {
  get errors() {
    return this.issues;
  }
  constructor(issues) {
    super();
    this.issues = [];
    this.addIssue = (sub) => {
      this.issues = [...this.issues, sub];
    };
    this.addIssues = (subs = []) => {
      this.issues = [...this.issues, ...subs];
    };
    const actualProto = new.target.prototype;
    if (Object.setPrototypeOf) {
      Object.setPrototypeOf(this, actualProto);
    } else {
      this.__proto__ = actualProto;
    }
    this.name = "ZodError";
    this.issues = issues;
  }
  format(_mapper) {
    const mapper = _mapper || function(issue) {
      return issue.message;
    };
    const fieldErrors = { _errors: [] };
    const processError = (error) => {
      for (const issue of error.issues) {
        if (issue.code === "invalid_union") {
          issue.unionErrors.map(processError);
        } else if (issue.code === "invalid_return_type") {
          processError(issue.returnTypeError);
        } else if (issue.code === "invalid_arguments") {
          processError(issue.argumentsError);
        } else if (issue.path.length === 0) {
          fieldErrors._errors.push(mapper(issue));
        } else {
          let curr = fieldErrors;
          let i = 0;
          while (i < issue.path.length) {
            const el = issue.path[i];
            const terminal = i === issue.path.length - 1;
            if (!terminal) {
              curr[el] = curr[el] || { _errors: [] };
            } else {
              curr[el] = curr[el] || { _errors: [] };
              curr[el]._errors.push(mapper(issue));
            }
            curr = curr[el];
            i++;
          }
        }
      }
    };
    processError(this);
    return fieldErrors;
  }
  static assert(value) {
    if (!(value instanceof _ZodError)) {
      throw new Error(`Not a ZodError: ${value}`);
    }
  }
  toString() {
    return this.message;
  }
  get message() {
    return JSON.stringify(this.issues, util.jsonStringifyReplacer, 2);
  }
  get isEmpty() {
    return this.issues.length === 0;
  }
  flatten(mapper = (issue) => issue.message) {
    const fieldErrors = {};
    const formErrors = [];
    for (const sub of this.issues) {
      if (sub.path.length > 0) {
        const firstEl = sub.path[0];
        fieldErrors[firstEl] = fieldErrors[firstEl] || [];
        fieldErrors[firstEl].push(mapper(sub));
      } else {
        formErrors.push(mapper(sub));
      }
    }
    return { formErrors, fieldErrors };
  }
  get formErrors() {
    return this.flatten();
  }
};
ZodError.create = (issues) => {
  const error = new ZodError(issues);
  return error;
};

// node_modules/zod/v3/locales/en.js
var errorMap = (issue, _ctx) => {
  let message;
  switch (issue.code) {
    case ZodIssueCode.invalid_type:
      if (issue.received === ZodParsedType.undefined) {
        message = "Required";
      } else {
        message = `Expected ${issue.expected}, received ${issue.received}`;
      }
      break;
    case ZodIssueCode.invalid_literal:
      message = `Invalid literal value, expected ${JSON.stringify(issue.expected, util.jsonStringifyReplacer)}`;
      break;
    case ZodIssueCode.unrecognized_keys:
      message = `Unrecognized key(s) in object: ${util.joinValues(issue.keys, ", ")}`;
      break;
    case ZodIssueCode.invalid_union:
      message = `Invalid input`;
      break;
    case ZodIssueCode.invalid_union_discriminator:
      message = `Invalid discriminator value. Expected ${util.joinValues(issue.options)}`;
      break;
    case ZodIssueCode.invalid_enum_value:
      message = `Invalid enum value. Expected ${util.joinValues(issue.options)}, received '${issue.received}'`;
      break;
    case ZodIssueCode.invalid_arguments:
      message = `Invalid function arguments`;
      break;
    case ZodIssueCode.invalid_return_type:
      message = `Invalid function return type`;
      break;
    case ZodIssueCode.invalid_date:
      message = `Invalid date`;
      break;
    case ZodIssueCode.invalid_string:
      if (typeof issue.validation === "object") {
        if ("includes" in issue.validation) {
          message = `Invalid input: must include "${issue.validation.includes}"`;
          if (typeof issue.validation.position === "number") {
            message = `${message} at one or more positions greater than or equal to ${issue.validation.position}`;
          }
        } else if ("startsWith" in issue.validation) {
          message = `Invalid input: must start with "${issue.validation.startsWith}"`;
        } else if ("endsWith" in issue.validation) {
          message = `Invalid input: must end with "${issue.validation.endsWith}"`;
        } else {
          util.assertNever(issue.validation);
        }
      } else if (issue.validation !== "regex") {
        message = `Invalid ${issue.validation}`;
      } else {
        message = "Invalid";
      }
      break;
    case ZodIssueCode.too_small:
      if (issue.type === "array")
        message = `Array must contain ${issue.exact ? "exactly" : issue.inclusive ? `at least` : `more than`} ${issue.minimum} element(s)`;
      else if (issue.type === "string")
        message = `String must contain ${issue.exact ? "exactly" : issue.inclusive ? `at least` : `over`} ${issue.minimum} character(s)`;
      else if (issue.type === "number")
        message = `Number must be ${issue.exact ? `exactly equal to ` : issue.inclusive ? `greater than or equal to ` : `greater than `}${issue.minimum}`;
      else if (issue.type === "bigint")
        message = `Number must be ${issue.exact ? `exactly equal to ` : issue.inclusive ? `greater than or equal to ` : `greater than `}${issue.minimum}`;
      else if (issue.type === "date")
        message = `Date must be ${issue.exact ? `exactly equal to ` : issue.inclusive ? `greater than or equal to ` : `greater than `}${new Date(Number(issue.minimum))}`;
      else
        message = "Invalid input";
      break;
    case ZodIssueCode.too_big:
      if (issue.type === "array")
        message = `Array must contain ${issue.exact ? `exactly` : issue.inclusive ? `at most` : `less than`} ${issue.maximum} element(s)`;
      else if (issue.type === "string")
        message = `String must contain ${issue.exact ? `exactly` : issue.inclusive ? `at most` : `under`} ${issue.maximum} character(s)`;
      else if (issue.type === "number")
        message = `Number must be ${issue.exact ? `exactly` : issue.inclusive ? `less than or equal to` : `less than`} ${issue.maximum}`;
      else if (issue.type === "bigint")
        message = `BigInt must be ${issue.exact ? `exactly` : issue.inclusive ? `less than or equal to` : `less than`} ${issue.maximum}`;
      else if (issue.type === "date")
        message = `Date must be ${issue.exact ? `exactly` : issue.inclusive ? `smaller than or equal to` : `smaller than`} ${new Date(Number(issue.maximum))}`;
      else
        message = "Invalid input";
      break;
    case ZodIssueCode.custom:
      message = `Invalid input`;
      break;
    case ZodIssueCode.invalid_intersection_types:
      message = `Intersection results could not be merged`;
      break;
    case ZodIssueCode.not_multiple_of:
      message = `Number must be a multiple of ${issue.multipleOf}`;
      break;
    case ZodIssueCode.not_finite:
      message = "Number must be finite";
      break;
    default:
      message = _ctx.defaultError;
      util.assertNever(issue);
  }
  return { message };
};
var en_default = errorMap;

// node_modules/zod/v3/errors.js
var overrideErrorMap = en_default;
function setErrorMap(map) {
  overrideErrorMap = map;
}
function getErrorMap() {
  return overrideErrorMap;
}

// node_modules/zod/v3/helpers/parseUtil.js
var makeIssue = (params) => {
  const { data, path, errorMaps, issueData } = params;
  const fullPath = [...path, ...issueData.path || []];
  const fullIssue = {
    ...issueData,
    path: fullPath
  };
  if (issueData.message !== void 0) {
    return {
      ...issueData,
      path: fullPath,
      message: issueData.message
    };
  }
  let errorMessage = "";
  const maps = errorMaps.filter((m) => !!m).slice().reverse();
  for (const map of maps) {
    errorMessage = map(fullIssue, { data, defaultError: errorMessage }).message;
  }
  return {
    ...issueData,
    path: fullPath,
    message: errorMessage
  };
};
var EMPTY_PATH = [];
function addIssueToContext(ctx, issueData) {
  const overrideMap = getErrorMap();
  const issue = makeIssue({
    issueData,
    data: ctx.data,
    path: ctx.path,
    errorMaps: [
      ctx.common.contextualErrorMap,
      // contextual error map is first priority
      ctx.schemaErrorMap,
      // then schema-bound map if available
      overrideMap,
      // then global override map
      overrideMap === en_default ? void 0 : en_default
      // then global default map
    ].filter((x) => !!x)
  });
  ctx.common.issues.push(issue);
}
var ParseStatus = class _ParseStatus {
  constructor() {
    this.value = "valid";
  }
  dirty() {
    if (this.value === "valid")
      this.value = "dirty";
  }
  abort() {
    if (this.value !== "aborted")
      this.value = "aborted";
  }
  static mergeArray(status, results) {
    const arrayValue = [];
    for (const s of results) {
      if (s.status === "aborted")
        return INVALID;
      if (s.status === "dirty")
        status.dirty();
      arrayValue.push(s.value);
    }
    return { status: status.value, value: arrayValue };
  }
  static async mergeObjectAsync(status, pairs) {
    const syncPairs = [];
    for (const pair of pairs) {
      const key = await pair.key;
      const value = await pair.value;
      syncPairs.push({
        key,
        value
      });
    }
    return _ParseStatus.mergeObjectSync(status, syncPairs);
  }
  static mergeObjectSync(status, pairs) {
    const finalObject = {};
    for (const pair of pairs) {
      const { key, value } = pair;
      if (key.status === "aborted")
        return INVALID;
      if (value.status === "aborted")
        return INVALID;
      if (key.status === "dirty")
        status.dirty();
      if (value.status === "dirty")
        status.dirty();
      if (key.value !== "__proto__" && (typeof value.value !== "undefined" || pair.alwaysSet)) {
        finalObject[key.value] = value.value;
      }
    }
    return { status: status.value, value: finalObject };
  }
};
var INVALID = Object.freeze({
  status: "aborted"
});
var DIRTY = (value) => ({ status: "dirty", value });
var OK = (value) => ({ status: "valid", value });
var isAborted = (x) => x.status === "aborted";
var isDirty = (x) => x.status === "dirty";
var isValid = (x) => x.status === "valid";
var isAsync = (x) => typeof Promise !== "undefined" && x instanceof Promise;

// node_modules/zod/v3/helpers/errorUtil.js
var errorUtil;
(function(errorUtil2) {
  errorUtil2.errToObj = (message) => typeof message === "string" ? { message } : message || {};
  errorUtil2.toString = (message) => typeof message === "string" ? message : message?.message;
})(errorUtil || (errorUtil = {}));

// node_modules/zod/v3/types.js
var ParseInputLazyPath = class {
  constructor(parent, value, path, key) {
    this._cachedPath = [];
    this.parent = parent;
    this.data = value;
    this._path = path;
    this._key = key;
  }
  get path() {
    if (!this._cachedPath.length) {
      if (Array.isArray(this._key)) {
        this._cachedPath.push(...this._path, ...this._key);
      } else {
        this._cachedPath.push(...this._path, this._key);
      }
    }
    return this._cachedPath;
  }
};
var handleResult = (ctx, result) => {
  if (isValid(result)) {
    return { success: true, data: result.value };
  } else {
    if (!ctx.common.issues.length) {
      throw new Error("Validation failed but no issues detected.");
    }
    return {
      success: false,
      get error() {
        if (this._error)
          return this._error;
        const error = new ZodError(ctx.common.issues);
        this._error = error;
        return this._error;
      }
    };
  }
};
function processCreateParams(params) {
  if (!params)
    return {};
  const { errorMap: errorMap2, invalid_type_error, required_error, description } = params;
  if (errorMap2 && (invalid_type_error || required_error)) {
    throw new Error(`Can't use "invalid_type_error" or "required_error" in conjunction with custom error map.`);
  }
  if (errorMap2)
    return { errorMap: errorMap2, description };
  const customMap = (iss, ctx) => {
    const { message } = params;
    if (iss.code === "invalid_enum_value") {
      return { message: message ?? ctx.defaultError };
    }
    if (typeof ctx.data === "undefined") {
      return { message: message ?? required_error ?? ctx.defaultError };
    }
    if (iss.code !== "invalid_type")
      return { message: ctx.defaultError };
    return { message: message ?? invalid_type_error ?? ctx.defaultError };
  };
  return { errorMap: customMap, description };
}
var ZodType = class {
  get description() {
    return this._def.description;
  }
  _getType(input) {
    return getParsedType(input.data);
  }
  _getOrReturnCtx(input, ctx) {
    return ctx || {
      common: input.parent.common,
      data: input.data,
      parsedType: getParsedType(input.data),
      schemaErrorMap: this._def.errorMap,
      path: input.path,
      parent: input.parent
    };
  }
  _processInputParams(input) {
    return {
      status: new ParseStatus(),
      ctx: {
        common: input.parent.common,
        data: input.data,
        parsedType: getParsedType(input.data),
        schemaErrorMap: this._def.errorMap,
        path: input.path,
        parent: input.parent
      }
    };
  }
  _parseSync(input) {
    const result = this._parse(input);
    if (isAsync(result)) {
      throw new Error("Synchronous parse encountered promise.");
    }
    return result;
  }
  _parseAsync(input) {
    const result = this._parse(input);
    return Promise.resolve(result);
  }
  parse(data, params) {
    const result = this.safeParse(data, params);
    if (result.success)
      return result.data;
    throw result.error;
  }
  safeParse(data, params) {
    const ctx = {
      common: {
        issues: [],
        async: params?.async ?? false,
        contextualErrorMap: params?.errorMap
      },
      path: params?.path || [],
      schemaErrorMap: this._def.errorMap,
      parent: null,
      data,
      parsedType: getParsedType(data)
    };
    const result = this._parseSync({ data, path: ctx.path, parent: ctx });
    return handleResult(ctx, result);
  }
  "~validate"(data) {
    const ctx = {
      common: {
        issues: [],
        async: !!this["~standard"].async
      },
      path: [],
      schemaErrorMap: this._def.errorMap,
      parent: null,
      data,
      parsedType: getParsedType(data)
    };
    if (!this["~standard"].async) {
      try {
        const result = this._parseSync({ data, path: [], parent: ctx });
        return isValid(result) ? {
          value: result.value
        } : {
          issues: ctx.common.issues
        };
      } catch (err) {
        if (err?.message?.toLowerCase()?.includes("encountered")) {
          this["~standard"].async = true;
        }
        ctx.common = {
          issues: [],
          async: true
        };
      }
    }
    return this._parseAsync({ data, path: [], parent: ctx }).then((result) => isValid(result) ? {
      value: result.value
    } : {
      issues: ctx.common.issues
    });
  }
  async parseAsync(data, params) {
    const result = await this.safeParseAsync(data, params);
    if (result.success)
      return result.data;
    throw result.error;
  }
  async safeParseAsync(data, params) {
    const ctx = {
      common: {
        issues: [],
        contextualErrorMap: params?.errorMap,
        async: true
      },
      path: params?.path || [],
      schemaErrorMap: this._def.errorMap,
      parent: null,
      data,
      parsedType: getParsedType(data)
    };
    const maybeAsyncResult = this._parse({ data, path: ctx.path, parent: ctx });
    const result = await (isAsync(maybeAsyncResult) ? maybeAsyncResult : Promise.resolve(maybeAsyncResult));
    return handleResult(ctx, result);
  }
  refine(check, message) {
    const getIssueProperties = (val) => {
      if (typeof message === "string" || typeof message === "undefined") {
        return { message };
      } else if (typeof message === "function") {
        return message(val);
      } else {
        return message;
      }
    };
    return this._refinement((val, ctx) => {
      const result = check(val);
      const setError = () => ctx.addIssue({
        code: ZodIssueCode.custom,
        ...getIssueProperties(val)
      });
      if (typeof Promise !== "undefined" && result instanceof Promise) {
        return result.then((data) => {
          if (!data) {
            setError();
            return false;
          } else {
            return true;
          }
        });
      }
      if (!result) {
        setError();
        return false;
      } else {
        return true;
      }
    });
  }
  refinement(check, refinementData) {
    return this._refinement((val, ctx) => {
      if (!check(val)) {
        ctx.addIssue(typeof refinementData === "function" ? refinementData(val, ctx) : refinementData);
        return false;
      } else {
        return true;
      }
    });
  }
  _refinement(refinement) {
    return new ZodEffects({
      schema: this,
      typeName: ZodFirstPartyTypeKind.ZodEffects,
      effect: { type: "refinement", refinement }
    });
  }
  superRefine(refinement) {
    return this._refinement(refinement);
  }
  constructor(def) {
    this.spa = this.safeParseAsync;
    this._def = def;
    this.parse = this.parse.bind(this);
    this.safeParse = this.safeParse.bind(this);
    this.parseAsync = this.parseAsync.bind(this);
    this.safeParseAsync = this.safeParseAsync.bind(this);
    this.spa = this.spa.bind(this);
    this.refine = this.refine.bind(this);
    this.refinement = this.refinement.bind(this);
    this.superRefine = this.superRefine.bind(this);
    this.optional = this.optional.bind(this);
    this.nullable = this.nullable.bind(this);
    this.nullish = this.nullish.bind(this);
    this.array = this.array.bind(this);
    this.promise = this.promise.bind(this);
    this.or = this.or.bind(this);
    this.and = this.and.bind(this);
    this.transform = this.transform.bind(this);
    this.brand = this.brand.bind(this);
    this.default = this.default.bind(this);
    this.catch = this.catch.bind(this);
    this.describe = this.describe.bind(this);
    this.pipe = this.pipe.bind(this);
    this.readonly = this.readonly.bind(this);
    this.isNullable = this.isNullable.bind(this);
    this.isOptional = this.isOptional.bind(this);
    this["~standard"] = {
      version: 1,
      vendor: "zod",
      validate: (data) => this["~validate"](data)
    };
  }
  optional() {
    return ZodOptional.create(this, this._def);
  }
  nullable() {
    return ZodNullable.create(this, this._def);
  }
  nullish() {
    return this.nullable().optional();
  }
  array() {
    return ZodArray.create(this);
  }
  promise() {
    return ZodPromise.create(this, this._def);
  }
  or(option) {
    return ZodUnion.create([this, option], this._def);
  }
  and(incoming) {
    return ZodIntersection.create(this, incoming, this._def);
  }
  transform(transform) {
    return new ZodEffects({
      ...processCreateParams(this._def),
      schema: this,
      typeName: ZodFirstPartyTypeKind.ZodEffects,
      effect: { type: "transform", transform }
    });
  }
  default(def) {
    const defaultValueFunc = typeof def === "function" ? def : () => def;
    return new ZodDefault({
      ...processCreateParams(this._def),
      innerType: this,
      defaultValue: defaultValueFunc,
      typeName: ZodFirstPartyTypeKind.ZodDefault
    });
  }
  brand() {
    return new ZodBranded({
      typeName: ZodFirstPartyTypeKind.ZodBranded,
      type: this,
      ...processCreateParams(this._def)
    });
  }
  catch(def) {
    const catchValueFunc = typeof def === "function" ? def : () => def;
    return new ZodCatch({
      ...processCreateParams(this._def),
      innerType: this,
      catchValue: catchValueFunc,
      typeName: ZodFirstPartyTypeKind.ZodCatch
    });
  }
  describe(description) {
    const This = this.constructor;
    return new This({
      ...this._def,
      description
    });
  }
  pipe(target) {
    return ZodPipeline.create(this, target);
  }
  readonly() {
    return ZodReadonly.create(this);
  }
  isOptional() {
    return this.safeParse(void 0).success;
  }
  isNullable() {
    return this.safeParse(null).success;
  }
};
var cuidRegex = /^c[^\s-]{8,}$/i;
var cuid2Regex = /^[0-9a-z]+$/;
var ulidRegex = /^[0-9A-HJKMNP-TV-Z]{26}$/i;
var uuidRegex = /^[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}$/i;
var nanoidRegex = /^[a-z0-9_-]{21}$/i;
var jwtRegex = /^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$/;
var durationRegex = /^[-+]?P(?!$)(?:(?:[-+]?\d+Y)|(?:[-+]?\d+[.,]\d+Y$))?(?:(?:[-+]?\d+M)|(?:[-+]?\d+[.,]\d+M$))?(?:(?:[-+]?\d+W)|(?:[-+]?\d+[.,]\d+W$))?(?:(?:[-+]?\d+D)|(?:[-+]?\d+[.,]\d+D$))?(?:T(?=[\d+-])(?:(?:[-+]?\d+H)|(?:[-+]?\d+[.,]\d+H$))?(?:(?:[-+]?\d+M)|(?:[-+]?\d+[.,]\d+M$))?(?:[-+]?\d+(?:[.,]\d+)?S)?)??$/;
var emailRegex = /^(?!\.)(?!.*\.\.)([A-Z0-9_'+\-\.]*)[A-Z0-9_+-]@([A-Z0-9][A-Z0-9\-]*\.)+[A-Z]{2,}$/i;
var _emojiRegex = `^(\\p{Extended_Pictographic}|\\p{Emoji_Component})+$`;
var emojiRegex;
var ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])$/;
var ipv4CidrRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\/(3[0-2]|[12]?[0-9])$/;
var ipv6Regex = /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$/;
var ipv6CidrRegex = /^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\/(12[0-8]|1[01][0-9]|[1-9]?[0-9])$/;
var base64Regex = /^([0-9a-zA-Z+/]{4})*(([0-9a-zA-Z+/]{2}==)|([0-9a-zA-Z+/]{3}=))?$/;
var base64urlRegex = /^([0-9a-zA-Z-_]{4})*(([0-9a-zA-Z-_]{2}(==)?)|([0-9a-zA-Z-_]{3}(=)?))?$/;
var dateRegexSource = `((\\d\\d[2468][048]|\\d\\d[13579][26]|\\d\\d0[48]|[02468][048]00|[13579][26]00)-02-29|\\d{4}-((0[13578]|1[02])-(0[1-9]|[12]\\d|3[01])|(0[469]|11)-(0[1-9]|[12]\\d|30)|(02)-(0[1-9]|1\\d|2[0-8])))`;
var dateRegex = new RegExp(`^${dateRegexSource}$`);
function timeRegexSource(args) {
  let secondsRegexSource = `[0-5]\\d`;
  if (args.precision) {
    secondsRegexSource = `${secondsRegexSource}\\.\\d{${args.precision}}`;
  } else if (args.precision == null) {
    secondsRegexSource = `${secondsRegexSource}(\\.\\d+)?`;
  }
  const secondsQuantifier = args.precision ? "+" : "?";
  return `([01]\\d|2[0-3]):[0-5]\\d(:${secondsRegexSource})${secondsQuantifier}`;
}
function timeRegex(args) {
  return new RegExp(`^${timeRegexSource(args)}$`);
}
function datetimeRegex(args) {
  let regex = `${dateRegexSource}T${timeRegexSource(args)}`;
  const opts = [];
  opts.push(args.local ? `Z?` : `Z`);
  if (args.offset)
    opts.push(`([+-]\\d{2}:?\\d{2})`);
  regex = `${regex}(${opts.join("|")})`;
  return new RegExp(`^${regex}$`);
}
function isValidIP(ip, version) {
  if ((version === "v4" || !version) && ipv4Regex.test(ip)) {
    return true;
  }
  if ((version === "v6" || !version) && ipv6Regex.test(ip)) {
    return true;
  }
  return false;
}
function isValidJWT(jwt, alg) {
  if (!jwtRegex.test(jwt))
    return false;
  try {
    const [header] = jwt.split(".");
    if (!header)
      return false;
    const base64 = header.replace(/-/g, "+").replace(/_/g, "/").padEnd(header.length + (4 - header.length % 4) % 4, "=");
    const decoded = JSON.parse(atob(base64));
    if (typeof decoded !== "object" || decoded === null)
      return false;
    if ("typ" in decoded && decoded?.typ !== "JWT")
      return false;
    if (!decoded.alg)
      return false;
    if (alg && decoded.alg !== alg)
      return false;
    return true;
  } catch {
    return false;
  }
}
function isValidCidr(ip, version) {
  if ((version === "v4" || !version) && ipv4CidrRegex.test(ip)) {
    return true;
  }
  if ((version === "v6" || !version) && ipv6CidrRegex.test(ip)) {
    return true;
  }
  return false;
}
var ZodString = class _ZodString extends ZodType {
  _parse(input) {
    if (this._def.coerce) {
      input.data = String(input.data);
    }
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.string) {
      const ctx2 = this._getOrReturnCtx(input);
      addIssueToContext(ctx2, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.string,
        received: ctx2.parsedType
      });
      return INVALID;
    }
    const status = new ParseStatus();
    let ctx = void 0;
    for (const check of this._def.checks) {
      if (check.kind === "min") {
        if (input.data.length < check.value) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.too_small,
            minimum: check.value,
            type: "string",
            inclusive: true,
            exact: false,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "max") {
        if (input.data.length > check.value) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.too_big,
            maximum: check.value,
            type: "string",
            inclusive: true,
            exact: false,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "length") {
        const tooBig = input.data.length > check.value;
        const tooSmall = input.data.length < check.value;
        if (tooBig || tooSmall) {
          ctx = this._getOrReturnCtx(input, ctx);
          if (tooBig) {
            addIssueToContext(ctx, {
              code: ZodIssueCode.too_big,
              maximum: check.value,
              type: "string",
              inclusive: true,
              exact: true,
              message: check.message
            });
          } else if (tooSmall) {
            addIssueToContext(ctx, {
              code: ZodIssueCode.too_small,
              minimum: check.value,
              type: "string",
              inclusive: true,
              exact: true,
              message: check.message
            });
          }
          status.dirty();
        }
      } else if (check.kind === "email") {
        if (!emailRegex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "email",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "emoji") {
        if (!emojiRegex) {
          emojiRegex = new RegExp(_emojiRegex, "u");
        }
        if (!emojiRegex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "emoji",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "uuid") {
        if (!uuidRegex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "uuid",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "nanoid") {
        if (!nanoidRegex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "nanoid",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "cuid") {
        if (!cuidRegex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "cuid",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "cuid2") {
        if (!cuid2Regex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "cuid2",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "ulid") {
        if (!ulidRegex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "ulid",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "url") {
        try {
          new URL(input.data);
        } catch {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "url",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "regex") {
        check.regex.lastIndex = 0;
        const testResult = check.regex.test(input.data);
        if (!testResult) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "regex",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "trim") {
        input.data = input.data.trim();
      } else if (check.kind === "includes") {
        if (!input.data.includes(check.value, check.position)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.invalid_string,
            validation: { includes: check.value, position: check.position },
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "toLowerCase") {
        input.data = input.data.toLowerCase();
      } else if (check.kind === "toUpperCase") {
        input.data = input.data.toUpperCase();
      } else if (check.kind === "startsWith") {
        if (!input.data.startsWith(check.value)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.invalid_string,
            validation: { startsWith: check.value },
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "endsWith") {
        if (!input.data.endsWith(check.value)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.invalid_string,
            validation: { endsWith: check.value },
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "datetime") {
        const regex = datetimeRegex(check);
        if (!regex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.invalid_string,
            validation: "datetime",
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "date") {
        const regex = dateRegex;
        if (!regex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.invalid_string,
            validation: "date",
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "time") {
        const regex = timeRegex(check);
        if (!regex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.invalid_string,
            validation: "time",
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "duration") {
        if (!durationRegex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "duration",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "ip") {
        if (!isValidIP(input.data, check.version)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "ip",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "jwt") {
        if (!isValidJWT(input.data, check.alg)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "jwt",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "cidr") {
        if (!isValidCidr(input.data, check.version)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "cidr",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "base64") {
        if (!base64Regex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "base64",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "base64url") {
        if (!base64urlRegex.test(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            validation: "base64url",
            code: ZodIssueCode.invalid_string,
            message: check.message
          });
          status.dirty();
        }
      } else {
        util.assertNever(check);
      }
    }
    return { status: status.value, value: input.data };
  }
  _regex(regex, validation, message) {
    return this.refinement((data) => regex.test(data), {
      validation,
      code: ZodIssueCode.invalid_string,
      ...errorUtil.errToObj(message)
    });
  }
  _addCheck(check) {
    return new _ZodString({
      ...this._def,
      checks: [...this._def.checks, check]
    });
  }
  email(message) {
    return this._addCheck({ kind: "email", ...errorUtil.errToObj(message) });
  }
  url(message) {
    return this._addCheck({ kind: "url", ...errorUtil.errToObj(message) });
  }
  emoji(message) {
    return this._addCheck({ kind: "emoji", ...errorUtil.errToObj(message) });
  }
  uuid(message) {
    return this._addCheck({ kind: "uuid", ...errorUtil.errToObj(message) });
  }
  nanoid(message) {
    return this._addCheck({ kind: "nanoid", ...errorUtil.errToObj(message) });
  }
  cuid(message) {
    return this._addCheck({ kind: "cuid", ...errorUtil.errToObj(message) });
  }
  cuid2(message) {
    return this._addCheck({ kind: "cuid2", ...errorUtil.errToObj(message) });
  }
  ulid(message) {
    return this._addCheck({ kind: "ulid", ...errorUtil.errToObj(message) });
  }
  base64(message) {
    return this._addCheck({ kind: "base64", ...errorUtil.errToObj(message) });
  }
  base64url(message) {
    return this._addCheck({
      kind: "base64url",
      ...errorUtil.errToObj(message)
    });
  }
  jwt(options) {
    return this._addCheck({ kind: "jwt", ...errorUtil.errToObj(options) });
  }
  ip(options) {
    return this._addCheck({ kind: "ip", ...errorUtil.errToObj(options) });
  }
  cidr(options) {
    return this._addCheck({ kind: "cidr", ...errorUtil.errToObj(options) });
  }
  datetime(options) {
    if (typeof options === "string") {
      return this._addCheck({
        kind: "datetime",
        precision: null,
        offset: false,
        local: false,
        message: options
      });
    }
    return this._addCheck({
      kind: "datetime",
      precision: typeof options?.precision === "undefined" ? null : options?.precision,
      offset: options?.offset ?? false,
      local: options?.local ?? false,
      ...errorUtil.errToObj(options?.message)
    });
  }
  date(message) {
    return this._addCheck({ kind: "date", message });
  }
  time(options) {
    if (typeof options === "string") {
      return this._addCheck({
        kind: "time",
        precision: null,
        message: options
      });
    }
    return this._addCheck({
      kind: "time",
      precision: typeof options?.precision === "undefined" ? null : options?.precision,
      ...errorUtil.errToObj(options?.message)
    });
  }
  duration(message) {
    return this._addCheck({ kind: "duration", ...errorUtil.errToObj(message) });
  }
  regex(regex, message) {
    return this._addCheck({
      kind: "regex",
      regex,
      ...errorUtil.errToObj(message)
    });
  }
  includes(value, options) {
    return this._addCheck({
      kind: "includes",
      value,
      position: options?.position,
      ...errorUtil.errToObj(options?.message)
    });
  }
  startsWith(value, message) {
    return this._addCheck({
      kind: "startsWith",
      value,
      ...errorUtil.errToObj(message)
    });
  }
  endsWith(value, message) {
    return this._addCheck({
      kind: "endsWith",
      value,
      ...errorUtil.errToObj(message)
    });
  }
  min(minLength, message) {
    return this._addCheck({
      kind: "min",
      value: minLength,
      ...errorUtil.errToObj(message)
    });
  }
  max(maxLength, message) {
    return this._addCheck({
      kind: "max",
      value: maxLength,
      ...errorUtil.errToObj(message)
    });
  }
  length(len, message) {
    return this._addCheck({
      kind: "length",
      value: len,
      ...errorUtil.errToObj(message)
    });
  }
  /**
   * Equivalent to `.min(1)`
   */
  nonempty(message) {
    return this.min(1, errorUtil.errToObj(message));
  }
  trim() {
    return new _ZodString({
      ...this._def,
      checks: [...this._def.checks, { kind: "trim" }]
    });
  }
  toLowerCase() {
    return new _ZodString({
      ...this._def,
      checks: [...this._def.checks, { kind: "toLowerCase" }]
    });
  }
  toUpperCase() {
    return new _ZodString({
      ...this._def,
      checks: [...this._def.checks, { kind: "toUpperCase" }]
    });
  }
  get isDatetime() {
    return !!this._def.checks.find((ch) => ch.kind === "datetime");
  }
  get isDate() {
    return !!this._def.checks.find((ch) => ch.kind === "date");
  }
  get isTime() {
    return !!this._def.checks.find((ch) => ch.kind === "time");
  }
  get isDuration() {
    return !!this._def.checks.find((ch) => ch.kind === "duration");
  }
  get isEmail() {
    return !!this._def.checks.find((ch) => ch.kind === "email");
  }
  get isURL() {
    return !!this._def.checks.find((ch) => ch.kind === "url");
  }
  get isEmoji() {
    return !!this._def.checks.find((ch) => ch.kind === "emoji");
  }
  get isUUID() {
    return !!this._def.checks.find((ch) => ch.kind === "uuid");
  }
  get isNANOID() {
    return !!this._def.checks.find((ch) => ch.kind === "nanoid");
  }
  get isCUID() {
    return !!this._def.checks.find((ch) => ch.kind === "cuid");
  }
  get isCUID2() {
    return !!this._def.checks.find((ch) => ch.kind === "cuid2");
  }
  get isULID() {
    return !!this._def.checks.find((ch) => ch.kind === "ulid");
  }
  get isIP() {
    return !!this._def.checks.find((ch) => ch.kind === "ip");
  }
  get isCIDR() {
    return !!this._def.checks.find((ch) => ch.kind === "cidr");
  }
  get isBase64() {
    return !!this._def.checks.find((ch) => ch.kind === "base64");
  }
  get isBase64url() {
    return !!this._def.checks.find((ch) => ch.kind === "base64url");
  }
  get minLength() {
    let min = null;
    for (const ch of this._def.checks) {
      if (ch.kind === "min") {
        if (min === null || ch.value > min)
          min = ch.value;
      }
    }
    return min;
  }
  get maxLength() {
    let max = null;
    for (const ch of this._def.checks) {
      if (ch.kind === "max") {
        if (max === null || ch.value < max)
          max = ch.value;
      }
    }
    return max;
  }
};
ZodString.create = (params) => {
  return new ZodString({
    checks: [],
    typeName: ZodFirstPartyTypeKind.ZodString,
    coerce: params?.coerce ?? false,
    ...processCreateParams(params)
  });
};
function floatSafeRemainder(val, step) {
  const valDecCount = (val.toString().split(".")[1] || "").length;
  const stepDecCount = (step.toString().split(".")[1] || "").length;
  const decCount = valDecCount > stepDecCount ? valDecCount : stepDecCount;
  const valInt = Number.parseInt(val.toFixed(decCount).replace(".", ""));
  const stepInt = Number.parseInt(step.toFixed(decCount).replace(".", ""));
  return valInt % stepInt / 10 ** decCount;
}
var ZodNumber = class _ZodNumber extends ZodType {
  constructor() {
    super(...arguments);
    this.min = this.gte;
    this.max = this.lte;
    this.step = this.multipleOf;
  }
  _parse(input) {
    if (this._def.coerce) {
      input.data = Number(input.data);
    }
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.number) {
      const ctx2 = this._getOrReturnCtx(input);
      addIssueToContext(ctx2, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.number,
        received: ctx2.parsedType
      });
      return INVALID;
    }
    let ctx = void 0;
    const status = new ParseStatus();
    for (const check of this._def.checks) {
      if (check.kind === "int") {
        if (!util.isInteger(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.invalid_type,
            expected: "integer",
            received: "float",
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "min") {
        const tooSmall = check.inclusive ? input.data < check.value : input.data <= check.value;
        if (tooSmall) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.too_small,
            minimum: check.value,
            type: "number",
            inclusive: check.inclusive,
            exact: false,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "max") {
        const tooBig = check.inclusive ? input.data > check.value : input.data >= check.value;
        if (tooBig) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.too_big,
            maximum: check.value,
            type: "number",
            inclusive: check.inclusive,
            exact: false,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "multipleOf") {
        if (floatSafeRemainder(input.data, check.value) !== 0) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.not_multiple_of,
            multipleOf: check.value,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "finite") {
        if (!Number.isFinite(input.data)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.not_finite,
            message: check.message
          });
          status.dirty();
        }
      } else {
        util.assertNever(check);
      }
    }
    return { status: status.value, value: input.data };
  }
  gte(value, message) {
    return this.setLimit("min", value, true, errorUtil.toString(message));
  }
  gt(value, message) {
    return this.setLimit("min", value, false, errorUtil.toString(message));
  }
  lte(value, message) {
    return this.setLimit("max", value, true, errorUtil.toString(message));
  }
  lt(value, message) {
    return this.setLimit("max", value, false, errorUtil.toString(message));
  }
  setLimit(kind, value, inclusive, message) {
    return new _ZodNumber({
      ...this._def,
      checks: [
        ...this._def.checks,
        {
          kind,
          value,
          inclusive,
          message: errorUtil.toString(message)
        }
      ]
    });
  }
  _addCheck(check) {
    return new _ZodNumber({
      ...this._def,
      checks: [...this._def.checks, check]
    });
  }
  int(message) {
    return this._addCheck({
      kind: "int",
      message: errorUtil.toString(message)
    });
  }
  positive(message) {
    return this._addCheck({
      kind: "min",
      value: 0,
      inclusive: false,
      message: errorUtil.toString(message)
    });
  }
  negative(message) {
    return this._addCheck({
      kind: "max",
      value: 0,
      inclusive: false,
      message: errorUtil.toString(message)
    });
  }
  nonpositive(message) {
    return this._addCheck({
      kind: "max",
      value: 0,
      inclusive: true,
      message: errorUtil.toString(message)
    });
  }
  nonnegative(message) {
    return this._addCheck({
      kind: "min",
      value: 0,
      inclusive: true,
      message: errorUtil.toString(message)
    });
  }
  multipleOf(value, message) {
    return this._addCheck({
      kind: "multipleOf",
      value,
      message: errorUtil.toString(message)
    });
  }
  finite(message) {
    return this._addCheck({
      kind: "finite",
      message: errorUtil.toString(message)
    });
  }
  safe(message) {
    return this._addCheck({
      kind: "min",
      inclusive: true,
      value: Number.MIN_SAFE_INTEGER,
      message: errorUtil.toString(message)
    })._addCheck({
      kind: "max",
      inclusive: true,
      value: Number.MAX_SAFE_INTEGER,
      message: errorUtil.toString(message)
    });
  }
  get minValue() {
    let min = null;
    for (const ch of this._def.checks) {
      if (ch.kind === "min") {
        if (min === null || ch.value > min)
          min = ch.value;
      }
    }
    return min;
  }
  get maxValue() {
    let max = null;
    for (const ch of this._def.checks) {
      if (ch.kind === "max") {
        if (max === null || ch.value < max)
          max = ch.value;
      }
    }
    return max;
  }
  get isInt() {
    return !!this._def.checks.find((ch) => ch.kind === "int" || ch.kind === "multipleOf" && util.isInteger(ch.value));
  }
  get isFinite() {
    let max = null;
    let min = null;
    for (const ch of this._def.checks) {
      if (ch.kind === "finite" || ch.kind === "int" || ch.kind === "multipleOf") {
        return true;
      } else if (ch.kind === "min") {
        if (min === null || ch.value > min)
          min = ch.value;
      } else if (ch.kind === "max") {
        if (max === null || ch.value < max)
          max = ch.value;
      }
    }
    return Number.isFinite(min) && Number.isFinite(max);
  }
};
ZodNumber.create = (params) => {
  return new ZodNumber({
    checks: [],
    typeName: ZodFirstPartyTypeKind.ZodNumber,
    coerce: params?.coerce || false,
    ...processCreateParams(params)
  });
};
var ZodBigInt = class _ZodBigInt extends ZodType {
  constructor() {
    super(...arguments);
    this.min = this.gte;
    this.max = this.lte;
  }
  _parse(input) {
    if (this._def.coerce) {
      try {
        input.data = BigInt(input.data);
      } catch {
        return this._getInvalidInput(input);
      }
    }
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.bigint) {
      return this._getInvalidInput(input);
    }
    let ctx = void 0;
    const status = new ParseStatus();
    for (const check of this._def.checks) {
      if (check.kind === "min") {
        const tooSmall = check.inclusive ? input.data < check.value : input.data <= check.value;
        if (tooSmall) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.too_small,
            type: "bigint",
            minimum: check.value,
            inclusive: check.inclusive,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "max") {
        const tooBig = check.inclusive ? input.data > check.value : input.data >= check.value;
        if (tooBig) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.too_big,
            type: "bigint",
            maximum: check.value,
            inclusive: check.inclusive,
            message: check.message
          });
          status.dirty();
        }
      } else if (check.kind === "multipleOf") {
        if (input.data % check.value !== BigInt(0)) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.not_multiple_of,
            multipleOf: check.value,
            message: check.message
          });
          status.dirty();
        }
      } else {
        util.assertNever(check);
      }
    }
    return { status: status.value, value: input.data };
  }
  _getInvalidInput(input) {
    const ctx = this._getOrReturnCtx(input);
    addIssueToContext(ctx, {
      code: ZodIssueCode.invalid_type,
      expected: ZodParsedType.bigint,
      received: ctx.parsedType
    });
    return INVALID;
  }
  gte(value, message) {
    return this.setLimit("min", value, true, errorUtil.toString(message));
  }
  gt(value, message) {
    return this.setLimit("min", value, false, errorUtil.toString(message));
  }
  lte(value, message) {
    return this.setLimit("max", value, true, errorUtil.toString(message));
  }
  lt(value, message) {
    return this.setLimit("max", value, false, errorUtil.toString(message));
  }
  setLimit(kind, value, inclusive, message) {
    return new _ZodBigInt({
      ...this._def,
      checks: [
        ...this._def.checks,
        {
          kind,
          value,
          inclusive,
          message: errorUtil.toString(message)
        }
      ]
    });
  }
  _addCheck(check) {
    return new _ZodBigInt({
      ...this._def,
      checks: [...this._def.checks, check]
    });
  }
  positive(message) {
    return this._addCheck({
      kind: "min",
      value: BigInt(0),
      inclusive: false,
      message: errorUtil.toString(message)
    });
  }
  negative(message) {
    return this._addCheck({
      kind: "max",
      value: BigInt(0),
      inclusive: false,
      message: errorUtil.toString(message)
    });
  }
  nonpositive(message) {
    return this._addCheck({
      kind: "max",
      value: BigInt(0),
      inclusive: true,
      message: errorUtil.toString(message)
    });
  }
  nonnegative(message) {
    return this._addCheck({
      kind: "min",
      value: BigInt(0),
      inclusive: true,
      message: errorUtil.toString(message)
    });
  }
  multipleOf(value, message) {
    return this._addCheck({
      kind: "multipleOf",
      value,
      message: errorUtil.toString(message)
    });
  }
  get minValue() {
    let min = null;
    for (const ch of this._def.checks) {
      if (ch.kind === "min") {
        if (min === null || ch.value > min)
          min = ch.value;
      }
    }
    return min;
  }
  get maxValue() {
    let max = null;
    for (const ch of this._def.checks) {
      if (ch.kind === "max") {
        if (max === null || ch.value < max)
          max = ch.value;
      }
    }
    return max;
  }
};
ZodBigInt.create = (params) => {
  return new ZodBigInt({
    checks: [],
    typeName: ZodFirstPartyTypeKind.ZodBigInt,
    coerce: params?.coerce ?? false,
    ...processCreateParams(params)
  });
};
var ZodBoolean = class extends ZodType {
  _parse(input) {
    if (this._def.coerce) {
      input.data = Boolean(input.data);
    }
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.boolean) {
      const ctx = this._getOrReturnCtx(input);
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.boolean,
        received: ctx.parsedType
      });
      return INVALID;
    }
    return OK(input.data);
  }
};
ZodBoolean.create = (params) => {
  return new ZodBoolean({
    typeName: ZodFirstPartyTypeKind.ZodBoolean,
    coerce: params?.coerce || false,
    ...processCreateParams(params)
  });
};
var ZodDate = class _ZodDate extends ZodType {
  _parse(input) {
    if (this._def.coerce) {
      input.data = new Date(input.data);
    }
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.date) {
      const ctx2 = this._getOrReturnCtx(input);
      addIssueToContext(ctx2, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.date,
        received: ctx2.parsedType
      });
      return INVALID;
    }
    if (Number.isNaN(input.data.getTime())) {
      const ctx2 = this._getOrReturnCtx(input);
      addIssueToContext(ctx2, {
        code: ZodIssueCode.invalid_date
      });
      return INVALID;
    }
    const status = new ParseStatus();
    let ctx = void 0;
    for (const check of this._def.checks) {
      if (check.kind === "min") {
        if (input.data.getTime() < check.value) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.too_small,
            message: check.message,
            inclusive: true,
            exact: false,
            minimum: check.value,
            type: "date"
          });
          status.dirty();
        }
      } else if (check.kind === "max") {
        if (input.data.getTime() > check.value) {
          ctx = this._getOrReturnCtx(input, ctx);
          addIssueToContext(ctx, {
            code: ZodIssueCode.too_big,
            message: check.message,
            inclusive: true,
            exact: false,
            maximum: check.value,
            type: "date"
          });
          status.dirty();
        }
      } else {
        util.assertNever(check);
      }
    }
    return {
      status: status.value,
      value: new Date(input.data.getTime())
    };
  }
  _addCheck(check) {
    return new _ZodDate({
      ...this._def,
      checks: [...this._def.checks, check]
    });
  }
  min(minDate, message) {
    return this._addCheck({
      kind: "min",
      value: minDate.getTime(),
      message: errorUtil.toString(message)
    });
  }
  max(maxDate, message) {
    return this._addCheck({
      kind: "max",
      value: maxDate.getTime(),
      message: errorUtil.toString(message)
    });
  }
  get minDate() {
    let min = null;
    for (const ch of this._def.checks) {
      if (ch.kind === "min") {
        if (min === null || ch.value > min)
          min = ch.value;
      }
    }
    return min != null ? new Date(min) : null;
  }
  get maxDate() {
    let max = null;
    for (const ch of this._def.checks) {
      if (ch.kind === "max") {
        if (max === null || ch.value < max)
          max = ch.value;
      }
    }
    return max != null ? new Date(max) : null;
  }
};
ZodDate.create = (params) => {
  return new ZodDate({
    checks: [],
    coerce: params?.coerce || false,
    typeName: ZodFirstPartyTypeKind.ZodDate,
    ...processCreateParams(params)
  });
};
var ZodSymbol = class extends ZodType {
  _parse(input) {
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.symbol) {
      const ctx = this._getOrReturnCtx(input);
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.symbol,
        received: ctx.parsedType
      });
      return INVALID;
    }
    return OK(input.data);
  }
};
ZodSymbol.create = (params) => {
  return new ZodSymbol({
    typeName: ZodFirstPartyTypeKind.ZodSymbol,
    ...processCreateParams(params)
  });
};
var ZodUndefined = class extends ZodType {
  _parse(input) {
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.undefined) {
      const ctx = this._getOrReturnCtx(input);
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.undefined,
        received: ctx.parsedType
      });
      return INVALID;
    }
    return OK(input.data);
  }
};
ZodUndefined.create = (params) => {
  return new ZodUndefined({
    typeName: ZodFirstPartyTypeKind.ZodUndefined,
    ...processCreateParams(params)
  });
};
var ZodNull = class extends ZodType {
  _parse(input) {
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.null) {
      const ctx = this._getOrReturnCtx(input);
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.null,
        received: ctx.parsedType
      });
      return INVALID;
    }
    return OK(input.data);
  }
};
ZodNull.create = (params) => {
  return new ZodNull({
    typeName: ZodFirstPartyTypeKind.ZodNull,
    ...processCreateParams(params)
  });
};
var ZodAny = class extends ZodType {
  constructor() {
    super(...arguments);
    this._any = true;
  }
  _parse(input) {
    return OK(input.data);
  }
};
ZodAny.create = (params) => {
  return new ZodAny({
    typeName: ZodFirstPartyTypeKind.ZodAny,
    ...processCreateParams(params)
  });
};
var ZodUnknown = class extends ZodType {
  constructor() {
    super(...arguments);
    this._unknown = true;
  }
  _parse(input) {
    return OK(input.data);
  }
};
ZodUnknown.create = (params) => {
  return new ZodUnknown({
    typeName: ZodFirstPartyTypeKind.ZodUnknown,
    ...processCreateParams(params)
  });
};
var ZodNever = class extends ZodType {
  _parse(input) {
    const ctx = this._getOrReturnCtx(input);
    addIssueToContext(ctx, {
      code: ZodIssueCode.invalid_type,
      expected: ZodParsedType.never,
      received: ctx.parsedType
    });
    return INVALID;
  }
};
ZodNever.create = (params) => {
  return new ZodNever({
    typeName: ZodFirstPartyTypeKind.ZodNever,
    ...processCreateParams(params)
  });
};
var ZodVoid = class extends ZodType {
  _parse(input) {
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.undefined) {
      const ctx = this._getOrReturnCtx(input);
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.void,
        received: ctx.parsedType
      });
      return INVALID;
    }
    return OK(input.data);
  }
};
ZodVoid.create = (params) => {
  return new ZodVoid({
    typeName: ZodFirstPartyTypeKind.ZodVoid,
    ...processCreateParams(params)
  });
};
var ZodArray = class _ZodArray extends ZodType {
  _parse(input) {
    const { ctx, status } = this._processInputParams(input);
    const def = this._def;
    if (ctx.parsedType !== ZodParsedType.array) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.array,
        received: ctx.parsedType
      });
      return INVALID;
    }
    if (def.exactLength !== null) {
      const tooBig = ctx.data.length > def.exactLength.value;
      const tooSmall = ctx.data.length < def.exactLength.value;
      if (tooBig || tooSmall) {
        addIssueToContext(ctx, {
          code: tooBig ? ZodIssueCode.too_big : ZodIssueCode.too_small,
          minimum: tooSmall ? def.exactLength.value : void 0,
          maximum: tooBig ? def.exactLength.value : void 0,
          type: "array",
          inclusive: true,
          exact: true,
          message: def.exactLength.message
        });
        status.dirty();
      }
    }
    if (def.minLength !== null) {
      if (ctx.data.length < def.minLength.value) {
        addIssueToContext(ctx, {
          code: ZodIssueCode.too_small,
          minimum: def.minLength.value,
          type: "array",
          inclusive: true,
          exact: false,
          message: def.minLength.message
        });
        status.dirty();
      }
    }
    if (def.maxLength !== null) {
      if (ctx.data.length > def.maxLength.value) {
        addIssueToContext(ctx, {
          code: ZodIssueCode.too_big,
          maximum: def.maxLength.value,
          type: "array",
          inclusive: true,
          exact: false,
          message: def.maxLength.message
        });
        status.dirty();
      }
    }
    if (ctx.common.async) {
      return Promise.all([...ctx.data].map((item, i) => {
        return def.type._parseAsync(new ParseInputLazyPath(ctx, item, ctx.path, i));
      })).then((result2) => {
        return ParseStatus.mergeArray(status, result2);
      });
    }
    const result = [...ctx.data].map((item, i) => {
      return def.type._parseSync(new ParseInputLazyPath(ctx, item, ctx.path, i));
    });
    return ParseStatus.mergeArray(status, result);
  }
  get element() {
    return this._def.type;
  }
  min(minLength, message) {
    return new _ZodArray({
      ...this._def,
      minLength: { value: minLength, message: errorUtil.toString(message) }
    });
  }
  max(maxLength, message) {
    return new _ZodArray({
      ...this._def,
      maxLength: { value: maxLength, message: errorUtil.toString(message) }
    });
  }
  length(len, message) {
    return new _ZodArray({
      ...this._def,
      exactLength: { value: len, message: errorUtil.toString(message) }
    });
  }
  nonempty(message) {
    return this.min(1, message);
  }
};
ZodArray.create = (schema, params) => {
  return new ZodArray({
    type: schema,
    minLength: null,
    maxLength: null,
    exactLength: null,
    typeName: ZodFirstPartyTypeKind.ZodArray,
    ...processCreateParams(params)
  });
};
function deepPartialify(schema) {
  if (schema instanceof ZodObject) {
    const newShape = {};
    for (const key in schema.shape) {
      const fieldSchema = schema.shape[key];
      newShape[key] = ZodOptional.create(deepPartialify(fieldSchema));
    }
    return new ZodObject({
      ...schema._def,
      shape: () => newShape
    });
  } else if (schema instanceof ZodArray) {
    return new ZodArray({
      ...schema._def,
      type: deepPartialify(schema.element)
    });
  } else if (schema instanceof ZodOptional) {
    return ZodOptional.create(deepPartialify(schema.unwrap()));
  } else if (schema instanceof ZodNullable) {
    return ZodNullable.create(deepPartialify(schema.unwrap()));
  } else if (schema instanceof ZodTuple) {
    return ZodTuple.create(schema.items.map((item) => deepPartialify(item)));
  } else {
    return schema;
  }
}
var ZodObject = class _ZodObject extends ZodType {
  constructor() {
    super(...arguments);
    this._cached = null;
    this.nonstrict = this.passthrough;
    this.augment = this.extend;
  }
  _getCached() {
    if (this._cached !== null)
      return this._cached;
    const shape = this._def.shape();
    const keys = util.objectKeys(shape);
    this._cached = { shape, keys };
    return this._cached;
  }
  _parse(input) {
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.object) {
      const ctx2 = this._getOrReturnCtx(input);
      addIssueToContext(ctx2, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.object,
        received: ctx2.parsedType
      });
      return INVALID;
    }
    const { status, ctx } = this._processInputParams(input);
    const { shape, keys: shapeKeys } = this._getCached();
    const extraKeys = [];
    if (!(this._def.catchall instanceof ZodNever && this._def.unknownKeys === "strip")) {
      for (const key in ctx.data) {
        if (!shapeKeys.includes(key)) {
          extraKeys.push(key);
        }
      }
    }
    const pairs = [];
    for (const key of shapeKeys) {
      const keyValidator = shape[key];
      const value = ctx.data[key];
      pairs.push({
        key: { status: "valid", value: key },
        value: keyValidator._parse(new ParseInputLazyPath(ctx, value, ctx.path, key)),
        alwaysSet: key in ctx.data
      });
    }
    if (this._def.catchall instanceof ZodNever) {
      const unknownKeys = this._def.unknownKeys;
      if (unknownKeys === "passthrough") {
        for (const key of extraKeys) {
          pairs.push({
            key: { status: "valid", value: key },
            value: { status: "valid", value: ctx.data[key] }
          });
        }
      } else if (unknownKeys === "strict") {
        if (extraKeys.length > 0) {
          addIssueToContext(ctx, {
            code: ZodIssueCode.unrecognized_keys,
            keys: extraKeys
          });
          status.dirty();
        }
      } else if (unknownKeys === "strip") {
      } else {
        throw new Error(`Internal ZodObject error: invalid unknownKeys value.`);
      }
    } else {
      const catchall = this._def.catchall;
      for (const key of extraKeys) {
        const value = ctx.data[key];
        pairs.push({
          key: { status: "valid", value: key },
          value: catchall._parse(
            new ParseInputLazyPath(ctx, value, ctx.path, key)
            //, ctx.child(key), value, getParsedType(value)
          ),
          alwaysSet: key in ctx.data
        });
      }
    }
    if (ctx.common.async) {
      return Promise.resolve().then(async () => {
        const syncPairs = [];
        for (const pair of pairs) {
          const key = await pair.key;
          const value = await pair.value;
          syncPairs.push({
            key,
            value,
            alwaysSet: pair.alwaysSet
          });
        }
        return syncPairs;
      }).then((syncPairs) => {
        return ParseStatus.mergeObjectSync(status, syncPairs);
      });
    } else {
      return ParseStatus.mergeObjectSync(status, pairs);
    }
  }
  get shape() {
    return this._def.shape();
  }
  strict(message) {
    errorUtil.errToObj;
    return new _ZodObject({
      ...this._def,
      unknownKeys: "strict",
      ...message !== void 0 ? {
        errorMap: (issue, ctx) => {
          const defaultError = this._def.errorMap?.(issue, ctx).message ?? ctx.defaultError;
          if (issue.code === "unrecognized_keys")
            return {
              message: errorUtil.errToObj(message).message ?? defaultError
            };
          return {
            message: defaultError
          };
        }
      } : {}
    });
  }
  strip() {
    return new _ZodObject({
      ...this._def,
      unknownKeys: "strip"
    });
  }
  passthrough() {
    return new _ZodObject({
      ...this._def,
      unknownKeys: "passthrough"
    });
  }
  // const AugmentFactory =
  //   <Def extends ZodObjectDef>(def: Def) =>
  //   <Augmentation extends ZodRawShape>(
  //     augmentation: Augmentation
  //   ): ZodObject<
  //     extendShape<ReturnType<Def["shape"]>, Augmentation>,
  //     Def["unknownKeys"],
  //     Def["catchall"]
  //   > => {
  //     return new ZodObject({
  //       ...def,
  //       shape: () => ({
  //         ...def.shape(),
  //         ...augmentation,
  //       }),
  //     }) as any;
  //   };
  extend(augmentation) {
    return new _ZodObject({
      ...this._def,
      shape: () => ({
        ...this._def.shape(),
        ...augmentation
      })
    });
  }
  /**
   * Prior to zod@1.0.12 there was a bug in the
   * inferred type of merged objects. Please
   * upgrade if you are experiencing issues.
   */
  merge(merging) {
    const merged = new _ZodObject({
      unknownKeys: merging._def.unknownKeys,
      catchall: merging._def.catchall,
      shape: () => ({
        ...this._def.shape(),
        ...merging._def.shape()
      }),
      typeName: ZodFirstPartyTypeKind.ZodObject
    });
    return merged;
  }
  // merge<
  //   Incoming extends AnyZodObject,
  //   Augmentation extends Incoming["shape"],
  //   NewOutput extends {
  //     [k in keyof Augmentation | keyof Output]: k extends keyof Augmentation
  //       ? Augmentation[k]["_output"]
  //       : k extends keyof Output
  //       ? Output[k]
  //       : never;
  //   },
  //   NewInput extends {
  //     [k in keyof Augmentation | keyof Input]: k extends keyof Augmentation
  //       ? Augmentation[k]["_input"]
  //       : k extends keyof Input
  //       ? Input[k]
  //       : never;
  //   }
  // >(
  //   merging: Incoming
  // ): ZodObject<
  //   extendShape<T, ReturnType<Incoming["_def"]["shape"]>>,
  //   Incoming["_def"]["unknownKeys"],
  //   Incoming["_def"]["catchall"],
  //   NewOutput,
  //   NewInput
  // > {
  //   const merged: any = new ZodObject({
  //     unknownKeys: merging._def.unknownKeys,
  //     catchall: merging._def.catchall,
  //     shape: () =>
  //       objectUtil.mergeShapes(this._def.shape(), merging._def.shape()),
  //     typeName: ZodFirstPartyTypeKind.ZodObject,
  //   }) as any;
  //   return merged;
  // }
  setKey(key, schema) {
    return this.augment({ [key]: schema });
  }
  // merge<Incoming extends AnyZodObject>(
  //   merging: Incoming
  // ): //ZodObject<T & Incoming["_shape"], UnknownKeys, Catchall> = (merging) => {
  // ZodObject<
  //   extendShape<T, ReturnType<Incoming["_def"]["shape"]>>,
  //   Incoming["_def"]["unknownKeys"],
  //   Incoming["_def"]["catchall"]
  // > {
  //   // const mergedShape = objectUtil.mergeShapes(
  //   //   this._def.shape(),
  //   //   merging._def.shape()
  //   // );
  //   const merged: any = new ZodObject({
  //     unknownKeys: merging._def.unknownKeys,
  //     catchall: merging._def.catchall,
  //     shape: () =>
  //       objectUtil.mergeShapes(this._def.shape(), merging._def.shape()),
  //     typeName: ZodFirstPartyTypeKind.ZodObject,
  //   }) as any;
  //   return merged;
  // }
  catchall(index) {
    return new _ZodObject({
      ...this._def,
      catchall: index
    });
  }
  pick(mask) {
    const shape = {};
    for (const key of util.objectKeys(mask)) {
      if (mask[key] && this.shape[key]) {
        shape[key] = this.shape[key];
      }
    }
    return new _ZodObject({
      ...this._def,
      shape: () => shape
    });
  }
  omit(mask) {
    const shape = {};
    for (const key of util.objectKeys(this.shape)) {
      if (!mask[key]) {
        shape[key] = this.shape[key];
      }
    }
    return new _ZodObject({
      ...this._def,
      shape: () => shape
    });
  }
  /**
   * @deprecated
   */
  deepPartial() {
    return deepPartialify(this);
  }
  partial(mask) {
    const newShape = {};
    for (const key of util.objectKeys(this.shape)) {
      const fieldSchema = this.shape[key];
      if (mask && !mask[key]) {
        newShape[key] = fieldSchema;
      } else {
        newShape[key] = fieldSchema.optional();
      }
    }
    return new _ZodObject({
      ...this._def,
      shape: () => newShape
    });
  }
  required(mask) {
    const newShape = {};
    for (const key of util.objectKeys(this.shape)) {
      if (mask && !mask[key]) {
        newShape[key] = this.shape[key];
      } else {
        const fieldSchema = this.shape[key];
        let newField = fieldSchema;
        while (newField instanceof ZodOptional) {
          newField = newField._def.innerType;
        }
        newShape[key] = newField;
      }
    }
    return new _ZodObject({
      ...this._def,
      shape: () => newShape
    });
  }
  keyof() {
    return createZodEnum(util.objectKeys(this.shape));
  }
};
ZodObject.create = (shape, params) => {
  return new ZodObject({
    shape: () => shape,
    unknownKeys: "strip",
    catchall: ZodNever.create(),
    typeName: ZodFirstPartyTypeKind.ZodObject,
    ...processCreateParams(params)
  });
};
ZodObject.strictCreate = (shape, params) => {
  return new ZodObject({
    shape: () => shape,
    unknownKeys: "strict",
    catchall: ZodNever.create(),
    typeName: ZodFirstPartyTypeKind.ZodObject,
    ...processCreateParams(params)
  });
};
ZodObject.lazycreate = (shape, params) => {
  return new ZodObject({
    shape,
    unknownKeys: "strip",
    catchall: ZodNever.create(),
    typeName: ZodFirstPartyTypeKind.ZodObject,
    ...processCreateParams(params)
  });
};
var ZodUnion = class extends ZodType {
  _parse(input) {
    const { ctx } = this._processInputParams(input);
    const options = this._def.options;
    function handleResults(results) {
      for (const result of results) {
        if (result.result.status === "valid") {
          return result.result;
        }
      }
      for (const result of results) {
        if (result.result.status === "dirty") {
          ctx.common.issues.push(...result.ctx.common.issues);
          return result.result;
        }
      }
      const unionErrors = results.map((result) => new ZodError(result.ctx.common.issues));
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_union,
        unionErrors
      });
      return INVALID;
    }
    if (ctx.common.async) {
      return Promise.all(options.map(async (option) => {
        const childCtx = {
          ...ctx,
          common: {
            ...ctx.common,
            issues: []
          },
          parent: null
        };
        return {
          result: await option._parseAsync({
            data: ctx.data,
            path: ctx.path,
            parent: childCtx
          }),
          ctx: childCtx
        };
      })).then(handleResults);
    } else {
      let dirty = void 0;
      const issues = [];
      for (const option of options) {
        const childCtx = {
          ...ctx,
          common: {
            ...ctx.common,
            issues: []
          },
          parent: null
        };
        const result = option._parseSync({
          data: ctx.data,
          path: ctx.path,
          parent: childCtx
        });
        if (result.status === "valid") {
          return result;
        } else if (result.status === "dirty" && !dirty) {
          dirty = { result, ctx: childCtx };
        }
        if (childCtx.common.issues.length) {
          issues.push(childCtx.common.issues);
        }
      }
      if (dirty) {
        ctx.common.issues.push(...dirty.ctx.common.issues);
        return dirty.result;
      }
      const unionErrors = issues.map((issues2) => new ZodError(issues2));
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_union,
        unionErrors
      });
      return INVALID;
    }
  }
  get options() {
    return this._def.options;
  }
};
ZodUnion.create = (types, params) => {
  return new ZodUnion({
    options: types,
    typeName: ZodFirstPartyTypeKind.ZodUnion,
    ...processCreateParams(params)
  });
};
var getDiscriminator = (type) => {
  if (type instanceof ZodLazy) {
    return getDiscriminator(type.schema);
  } else if (type instanceof ZodEffects) {
    return getDiscriminator(type.innerType());
  } else if (type instanceof ZodLiteral) {
    return [type.value];
  } else if (type instanceof ZodEnum) {
    return type.options;
  } else if (type instanceof ZodNativeEnum) {
    return util.objectValues(type.enum);
  } else if (type instanceof ZodDefault) {
    return getDiscriminator(type._def.innerType);
  } else if (type instanceof ZodUndefined) {
    return [void 0];
  } else if (type instanceof ZodNull) {
    return [null];
  } else if (type instanceof ZodOptional) {
    return [void 0, ...getDiscriminator(type.unwrap())];
  } else if (type instanceof ZodNullable) {
    return [null, ...getDiscriminator(type.unwrap())];
  } else if (type instanceof ZodBranded) {
    return getDiscriminator(type.unwrap());
  } else if (type instanceof ZodReadonly) {
    return getDiscriminator(type.unwrap());
  } else if (type instanceof ZodCatch) {
    return getDiscriminator(type._def.innerType);
  } else {
    return [];
  }
};
var ZodDiscriminatedUnion = class _ZodDiscriminatedUnion extends ZodType {
  _parse(input) {
    const { ctx } = this._processInputParams(input);
    if (ctx.parsedType !== ZodParsedType.object) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.object,
        received: ctx.parsedType
      });
      return INVALID;
    }
    const discriminator = this.discriminator;
    const discriminatorValue = ctx.data[discriminator];
    const option = this.optionsMap.get(discriminatorValue);
    if (!option) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_union_discriminator,
        options: Array.from(this.optionsMap.keys()),
        path: [discriminator]
      });
      return INVALID;
    }
    if (ctx.common.async) {
      return option._parseAsync({
        data: ctx.data,
        path: ctx.path,
        parent: ctx
      });
    } else {
      return option._parseSync({
        data: ctx.data,
        path: ctx.path,
        parent: ctx
      });
    }
  }
  get discriminator() {
    return this._def.discriminator;
  }
  get options() {
    return this._def.options;
  }
  get optionsMap() {
    return this._def.optionsMap;
  }
  /**
   * The constructor of the discriminated union schema. Its behaviour is very similar to that of the normal z.union() constructor.
   * However, it only allows a union of objects, all of which need to share a discriminator property. This property must
   * have a different value for each object in the union.
   * @param discriminator the name of the discriminator property
   * @param types an array of object schemas
   * @param params
   */
  static create(discriminator, options, params) {
    const optionsMap = /* @__PURE__ */ new Map();
    for (const type of options) {
      const discriminatorValues = getDiscriminator(type.shape[discriminator]);
      if (!discriminatorValues.length) {
        throw new Error(`A discriminator value for key \`${discriminator}\` could not be extracted from all schema options`);
      }
      for (const value of discriminatorValues) {
        if (optionsMap.has(value)) {
          throw new Error(`Discriminator property ${String(discriminator)} has duplicate value ${String(value)}`);
        }
        optionsMap.set(value, type);
      }
    }
    return new _ZodDiscriminatedUnion({
      typeName: ZodFirstPartyTypeKind.ZodDiscriminatedUnion,
      discriminator,
      options,
      optionsMap,
      ...processCreateParams(params)
    });
  }
};
function mergeValues(a, b) {
  const aType = getParsedType(a);
  const bType = getParsedType(b);
  if (a === b) {
    return { valid: true, data: a };
  } else if (aType === ZodParsedType.object && bType === ZodParsedType.object) {
    const bKeys = util.objectKeys(b);
    const sharedKeys = util.objectKeys(a).filter((key) => bKeys.indexOf(key) !== -1);
    const newObj = { ...a, ...b };
    for (const key of sharedKeys) {
      const sharedValue = mergeValues(a[key], b[key]);
      if (!sharedValue.valid) {
        return { valid: false };
      }
      newObj[key] = sharedValue.data;
    }
    return { valid: true, data: newObj };
  } else if (aType === ZodParsedType.array && bType === ZodParsedType.array) {
    if (a.length !== b.length) {
      return { valid: false };
    }
    const newArray = [];
    for (let index = 0; index < a.length; index++) {
      const itemA = a[index];
      const itemB = b[index];
      const sharedValue = mergeValues(itemA, itemB);
      if (!sharedValue.valid) {
        return { valid: false };
      }
      newArray.push(sharedValue.data);
    }
    return { valid: true, data: newArray };
  } else if (aType === ZodParsedType.date && bType === ZodParsedType.date && +a === +b) {
    return { valid: true, data: a };
  } else {
    return { valid: false };
  }
}
var ZodIntersection = class extends ZodType {
  _parse(input) {
    const { status, ctx } = this._processInputParams(input);
    const handleParsed = (parsedLeft, parsedRight) => {
      if (isAborted(parsedLeft) || isAborted(parsedRight)) {
        return INVALID;
      }
      const merged = mergeValues(parsedLeft.value, parsedRight.value);
      if (!merged.valid) {
        addIssueToContext(ctx, {
          code: ZodIssueCode.invalid_intersection_types
        });
        return INVALID;
      }
      if (isDirty(parsedLeft) || isDirty(parsedRight)) {
        status.dirty();
      }
      return { status: status.value, value: merged.data };
    };
    if (ctx.common.async) {
      return Promise.all([
        this._def.left._parseAsync({
          data: ctx.data,
          path: ctx.path,
          parent: ctx
        }),
        this._def.right._parseAsync({
          data: ctx.data,
          path: ctx.path,
          parent: ctx
        })
      ]).then(([left, right]) => handleParsed(left, right));
    } else {
      return handleParsed(this._def.left._parseSync({
        data: ctx.data,
        path: ctx.path,
        parent: ctx
      }), this._def.right._parseSync({
        data: ctx.data,
        path: ctx.path,
        parent: ctx
      }));
    }
  }
};
ZodIntersection.create = (left, right, params) => {
  return new ZodIntersection({
    left,
    right,
    typeName: ZodFirstPartyTypeKind.ZodIntersection,
    ...processCreateParams(params)
  });
};
var ZodTuple = class _ZodTuple extends ZodType {
  _parse(input) {
    const { status, ctx } = this._processInputParams(input);
    if (ctx.parsedType !== ZodParsedType.array) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.array,
        received: ctx.parsedType
      });
      return INVALID;
    }
    if (ctx.data.length < this._def.items.length) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.too_small,
        minimum: this._def.items.length,
        inclusive: true,
        exact: false,
        type: "array"
      });
      return INVALID;
    }
    const rest = this._def.rest;
    if (!rest && ctx.data.length > this._def.items.length) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.too_big,
        maximum: this._def.items.length,
        inclusive: true,
        exact: false,
        type: "array"
      });
      status.dirty();
    }
    const items = [...ctx.data].map((item, itemIndex) => {
      const schema = this._def.items[itemIndex] || this._def.rest;
      if (!schema)
        return null;
      return schema._parse(new ParseInputLazyPath(ctx, item, ctx.path, itemIndex));
    }).filter((x) => !!x);
    if (ctx.common.async) {
      return Promise.all(items).then((results) => {
        return ParseStatus.mergeArray(status, results);
      });
    } else {
      return ParseStatus.mergeArray(status, items);
    }
  }
  get items() {
    return this._def.items;
  }
  rest(rest) {
    return new _ZodTuple({
      ...this._def,
      rest
    });
  }
};
ZodTuple.create = (schemas2, params) => {
  if (!Array.isArray(schemas2)) {
    throw new Error("You must pass an array of schemas to z.tuple([ ... ])");
  }
  return new ZodTuple({
    items: schemas2,
    typeName: ZodFirstPartyTypeKind.ZodTuple,
    rest: null,
    ...processCreateParams(params)
  });
};
var ZodRecord = class _ZodRecord extends ZodType {
  get keySchema() {
    return this._def.keyType;
  }
  get valueSchema() {
    return this._def.valueType;
  }
  _parse(input) {
    const { status, ctx } = this._processInputParams(input);
    if (ctx.parsedType !== ZodParsedType.object) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.object,
        received: ctx.parsedType
      });
      return INVALID;
    }
    const pairs = [];
    const keyType = this._def.keyType;
    const valueType = this._def.valueType;
    for (const key in ctx.data) {
      pairs.push({
        key: keyType._parse(new ParseInputLazyPath(ctx, key, ctx.path, key)),
        value: valueType._parse(new ParseInputLazyPath(ctx, ctx.data[key], ctx.path, key)),
        alwaysSet: key in ctx.data
      });
    }
    if (ctx.common.async) {
      return ParseStatus.mergeObjectAsync(status, pairs);
    } else {
      return ParseStatus.mergeObjectSync(status, pairs);
    }
  }
  get element() {
    return this._def.valueType;
  }
  static create(first, second, third) {
    if (second instanceof ZodType) {
      return new _ZodRecord({
        keyType: first,
        valueType: second,
        typeName: ZodFirstPartyTypeKind.ZodRecord,
        ...processCreateParams(third)
      });
    }
    return new _ZodRecord({
      keyType: ZodString.create(),
      valueType: first,
      typeName: ZodFirstPartyTypeKind.ZodRecord,
      ...processCreateParams(second)
    });
  }
};
var ZodMap = class extends ZodType {
  get keySchema() {
    return this._def.keyType;
  }
  get valueSchema() {
    return this._def.valueType;
  }
  _parse(input) {
    const { status, ctx } = this._processInputParams(input);
    if (ctx.parsedType !== ZodParsedType.map) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.map,
        received: ctx.parsedType
      });
      return INVALID;
    }
    const keyType = this._def.keyType;
    const valueType = this._def.valueType;
    const pairs = [...ctx.data.entries()].map(([key, value], index) => {
      return {
        key: keyType._parse(new ParseInputLazyPath(ctx, key, ctx.path, [index, "key"])),
        value: valueType._parse(new ParseInputLazyPath(ctx, value, ctx.path, [index, "value"]))
      };
    });
    if (ctx.common.async) {
      const finalMap = /* @__PURE__ */ new Map();
      return Promise.resolve().then(async () => {
        for (const pair of pairs) {
          const key = await pair.key;
          const value = await pair.value;
          if (key.status === "aborted" || value.status === "aborted") {
            return INVALID;
          }
          if (key.status === "dirty" || value.status === "dirty") {
            status.dirty();
          }
          finalMap.set(key.value, value.value);
        }
        return { status: status.value, value: finalMap };
      });
    } else {
      const finalMap = /* @__PURE__ */ new Map();
      for (const pair of pairs) {
        const key = pair.key;
        const value = pair.value;
        if (key.status === "aborted" || value.status === "aborted") {
          return INVALID;
        }
        if (key.status === "dirty" || value.status === "dirty") {
          status.dirty();
        }
        finalMap.set(key.value, value.value);
      }
      return { status: status.value, value: finalMap };
    }
  }
};
ZodMap.create = (keyType, valueType, params) => {
  return new ZodMap({
    valueType,
    keyType,
    typeName: ZodFirstPartyTypeKind.ZodMap,
    ...processCreateParams(params)
  });
};
var ZodSet = class _ZodSet extends ZodType {
  _parse(input) {
    const { status, ctx } = this._processInputParams(input);
    if (ctx.parsedType !== ZodParsedType.set) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.set,
        received: ctx.parsedType
      });
      return INVALID;
    }
    const def = this._def;
    if (def.minSize !== null) {
      if (ctx.data.size < def.minSize.value) {
        addIssueToContext(ctx, {
          code: ZodIssueCode.too_small,
          minimum: def.minSize.value,
          type: "set",
          inclusive: true,
          exact: false,
          message: def.minSize.message
        });
        status.dirty();
      }
    }
    if (def.maxSize !== null) {
      if (ctx.data.size > def.maxSize.value) {
        addIssueToContext(ctx, {
          code: ZodIssueCode.too_big,
          maximum: def.maxSize.value,
          type: "set",
          inclusive: true,
          exact: false,
          message: def.maxSize.message
        });
        status.dirty();
      }
    }
    const valueType = this._def.valueType;
    function finalizeSet(elements2) {
      const parsedSet = /* @__PURE__ */ new Set();
      for (const element of elements2) {
        if (element.status === "aborted")
          return INVALID;
        if (element.status === "dirty")
          status.dirty();
        parsedSet.add(element.value);
      }
      return { status: status.value, value: parsedSet };
    }
    const elements = [...ctx.data.values()].map((item, i) => valueType._parse(new ParseInputLazyPath(ctx, item, ctx.path, i)));
    if (ctx.common.async) {
      return Promise.all(elements).then((elements2) => finalizeSet(elements2));
    } else {
      return finalizeSet(elements);
    }
  }
  min(minSize, message) {
    return new _ZodSet({
      ...this._def,
      minSize: { value: minSize, message: errorUtil.toString(message) }
    });
  }
  max(maxSize, message) {
    return new _ZodSet({
      ...this._def,
      maxSize: { value: maxSize, message: errorUtil.toString(message) }
    });
  }
  size(size, message) {
    return this.min(size, message).max(size, message);
  }
  nonempty(message) {
    return this.min(1, message);
  }
};
ZodSet.create = (valueType, params) => {
  return new ZodSet({
    valueType,
    minSize: null,
    maxSize: null,
    typeName: ZodFirstPartyTypeKind.ZodSet,
    ...processCreateParams(params)
  });
};
var ZodFunction = class _ZodFunction extends ZodType {
  constructor() {
    super(...arguments);
    this.validate = this.implement;
  }
  _parse(input) {
    const { ctx } = this._processInputParams(input);
    if (ctx.parsedType !== ZodParsedType.function) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.function,
        received: ctx.parsedType
      });
      return INVALID;
    }
    function makeArgsIssue(args, error) {
      return makeIssue({
        data: args,
        path: ctx.path,
        errorMaps: [ctx.common.contextualErrorMap, ctx.schemaErrorMap, getErrorMap(), en_default].filter((x) => !!x),
        issueData: {
          code: ZodIssueCode.invalid_arguments,
          argumentsError: error
        }
      });
    }
    function makeReturnsIssue(returns, error) {
      return makeIssue({
        data: returns,
        path: ctx.path,
        errorMaps: [ctx.common.contextualErrorMap, ctx.schemaErrorMap, getErrorMap(), en_default].filter((x) => !!x),
        issueData: {
          code: ZodIssueCode.invalid_return_type,
          returnTypeError: error
        }
      });
    }
    const params = { errorMap: ctx.common.contextualErrorMap };
    const fn = ctx.data;
    if (this._def.returns instanceof ZodPromise) {
      const me = this;
      return OK(async function(...args) {
        const error = new ZodError([]);
        const parsedArgs = await me._def.args.parseAsync(args, params).catch((e) => {
          error.addIssue(makeArgsIssue(args, e));
          throw error;
        });
        const result = await Reflect.apply(fn, this, parsedArgs);
        const parsedReturns = await me._def.returns._def.type.parseAsync(result, params).catch((e) => {
          error.addIssue(makeReturnsIssue(result, e));
          throw error;
        });
        return parsedReturns;
      });
    } else {
      const me = this;
      return OK(function(...args) {
        const parsedArgs = me._def.args.safeParse(args, params);
        if (!parsedArgs.success) {
          throw new ZodError([makeArgsIssue(args, parsedArgs.error)]);
        }
        const result = Reflect.apply(fn, this, parsedArgs.data);
        const parsedReturns = me._def.returns.safeParse(result, params);
        if (!parsedReturns.success) {
          throw new ZodError([makeReturnsIssue(result, parsedReturns.error)]);
        }
        return parsedReturns.data;
      });
    }
  }
  parameters() {
    return this._def.args;
  }
  returnType() {
    return this._def.returns;
  }
  args(...items) {
    return new _ZodFunction({
      ...this._def,
      args: ZodTuple.create(items).rest(ZodUnknown.create())
    });
  }
  returns(returnType) {
    return new _ZodFunction({
      ...this._def,
      returns: returnType
    });
  }
  implement(func) {
    const validatedFunc = this.parse(func);
    return validatedFunc;
  }
  strictImplement(func) {
    const validatedFunc = this.parse(func);
    return validatedFunc;
  }
  static create(args, returns, params) {
    return new _ZodFunction({
      args: args ? args : ZodTuple.create([]).rest(ZodUnknown.create()),
      returns: returns || ZodUnknown.create(),
      typeName: ZodFirstPartyTypeKind.ZodFunction,
      ...processCreateParams(params)
    });
  }
};
var ZodLazy = class extends ZodType {
  get schema() {
    return this._def.getter();
  }
  _parse(input) {
    const { ctx } = this._processInputParams(input);
    const lazySchema = this._def.getter();
    return lazySchema._parse({ data: ctx.data, path: ctx.path, parent: ctx });
  }
};
ZodLazy.create = (getter, params) => {
  return new ZodLazy({
    getter,
    typeName: ZodFirstPartyTypeKind.ZodLazy,
    ...processCreateParams(params)
  });
};
var ZodLiteral = class extends ZodType {
  _parse(input) {
    if (input.data !== this._def.value) {
      const ctx = this._getOrReturnCtx(input);
      addIssueToContext(ctx, {
        received: ctx.data,
        code: ZodIssueCode.invalid_literal,
        expected: this._def.value
      });
      return INVALID;
    }
    return { status: "valid", value: input.data };
  }
  get value() {
    return this._def.value;
  }
};
ZodLiteral.create = (value, params) => {
  return new ZodLiteral({
    value,
    typeName: ZodFirstPartyTypeKind.ZodLiteral,
    ...processCreateParams(params)
  });
};
function createZodEnum(values, params) {
  return new ZodEnum({
    values,
    typeName: ZodFirstPartyTypeKind.ZodEnum,
    ...processCreateParams(params)
  });
}
var ZodEnum = class _ZodEnum extends ZodType {
  _parse(input) {
    if (typeof input.data !== "string") {
      const ctx = this._getOrReturnCtx(input);
      const expectedValues = this._def.values;
      addIssueToContext(ctx, {
        expected: util.joinValues(expectedValues),
        received: ctx.parsedType,
        code: ZodIssueCode.invalid_type
      });
      return INVALID;
    }
    if (!this._cache) {
      this._cache = new Set(this._def.values);
    }
    if (!this._cache.has(input.data)) {
      const ctx = this._getOrReturnCtx(input);
      const expectedValues = this._def.values;
      addIssueToContext(ctx, {
        received: ctx.data,
        code: ZodIssueCode.invalid_enum_value,
        options: expectedValues
      });
      return INVALID;
    }
    return OK(input.data);
  }
  get options() {
    return this._def.values;
  }
  get enum() {
    const enumValues = {};
    for (const val of this._def.values) {
      enumValues[val] = val;
    }
    return enumValues;
  }
  get Values() {
    const enumValues = {};
    for (const val of this._def.values) {
      enumValues[val] = val;
    }
    return enumValues;
  }
  get Enum() {
    const enumValues = {};
    for (const val of this._def.values) {
      enumValues[val] = val;
    }
    return enumValues;
  }
  extract(values, newDef = this._def) {
    return _ZodEnum.create(values, {
      ...this._def,
      ...newDef
    });
  }
  exclude(values, newDef = this._def) {
    return _ZodEnum.create(this.options.filter((opt) => !values.includes(opt)), {
      ...this._def,
      ...newDef
    });
  }
};
ZodEnum.create = createZodEnum;
var ZodNativeEnum = class extends ZodType {
  _parse(input) {
    const nativeEnumValues = util.getValidEnumValues(this._def.values);
    const ctx = this._getOrReturnCtx(input);
    if (ctx.parsedType !== ZodParsedType.string && ctx.parsedType !== ZodParsedType.number) {
      const expectedValues = util.objectValues(nativeEnumValues);
      addIssueToContext(ctx, {
        expected: util.joinValues(expectedValues),
        received: ctx.parsedType,
        code: ZodIssueCode.invalid_type
      });
      return INVALID;
    }
    if (!this._cache) {
      this._cache = new Set(util.getValidEnumValues(this._def.values));
    }
    if (!this._cache.has(input.data)) {
      const expectedValues = util.objectValues(nativeEnumValues);
      addIssueToContext(ctx, {
        received: ctx.data,
        code: ZodIssueCode.invalid_enum_value,
        options: expectedValues
      });
      return INVALID;
    }
    return OK(input.data);
  }
  get enum() {
    return this._def.values;
  }
};
ZodNativeEnum.create = (values, params) => {
  return new ZodNativeEnum({
    values,
    typeName: ZodFirstPartyTypeKind.ZodNativeEnum,
    ...processCreateParams(params)
  });
};
var ZodPromise = class extends ZodType {
  unwrap() {
    return this._def.type;
  }
  _parse(input) {
    const { ctx } = this._processInputParams(input);
    if (ctx.parsedType !== ZodParsedType.promise && ctx.common.async === false) {
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.promise,
        received: ctx.parsedType
      });
      return INVALID;
    }
    const promisified = ctx.parsedType === ZodParsedType.promise ? ctx.data : Promise.resolve(ctx.data);
    return OK(promisified.then((data) => {
      return this._def.type.parseAsync(data, {
        path: ctx.path,
        errorMap: ctx.common.contextualErrorMap
      });
    }));
  }
};
ZodPromise.create = (schema, params) => {
  return new ZodPromise({
    type: schema,
    typeName: ZodFirstPartyTypeKind.ZodPromise,
    ...processCreateParams(params)
  });
};
var ZodEffects = class extends ZodType {
  innerType() {
    return this._def.schema;
  }
  sourceType() {
    return this._def.schema._def.typeName === ZodFirstPartyTypeKind.ZodEffects ? this._def.schema.sourceType() : this._def.schema;
  }
  _parse(input) {
    const { status, ctx } = this._processInputParams(input);
    const effect = this._def.effect || null;
    const checkCtx = {
      addIssue: (arg) => {
        addIssueToContext(ctx, arg);
        if (arg.fatal) {
          status.abort();
        } else {
          status.dirty();
        }
      },
      get path() {
        return ctx.path;
      }
    };
    checkCtx.addIssue = checkCtx.addIssue.bind(checkCtx);
    if (effect.type === "preprocess") {
      const processed = effect.transform(ctx.data, checkCtx);
      if (ctx.common.async) {
        return Promise.resolve(processed).then(async (processed2) => {
          if (status.value === "aborted")
            return INVALID;
          const result = await this._def.schema._parseAsync({
            data: processed2,
            path: ctx.path,
            parent: ctx
          });
          if (result.status === "aborted")
            return INVALID;
          if (result.status === "dirty")
            return DIRTY(result.value);
          if (status.value === "dirty")
            return DIRTY(result.value);
          return result;
        });
      } else {
        if (status.value === "aborted")
          return INVALID;
        const result = this._def.schema._parseSync({
          data: processed,
          path: ctx.path,
          parent: ctx
        });
        if (result.status === "aborted")
          return INVALID;
        if (result.status === "dirty")
          return DIRTY(result.value);
        if (status.value === "dirty")
          return DIRTY(result.value);
        return result;
      }
    }
    if (effect.type === "refinement") {
      const executeRefinement = (acc) => {
        const result = effect.refinement(acc, checkCtx);
        if (ctx.common.async) {
          return Promise.resolve(result);
        }
        if (result instanceof Promise) {
          throw new Error("Async refinement encountered during synchronous parse operation. Use .parseAsync instead.");
        }
        return acc;
      };
      if (ctx.common.async === false) {
        const inner = this._def.schema._parseSync({
          data: ctx.data,
          path: ctx.path,
          parent: ctx
        });
        if (inner.status === "aborted")
          return INVALID;
        if (inner.status === "dirty")
          status.dirty();
        executeRefinement(inner.value);
        return { status: status.value, value: inner.value };
      } else {
        return this._def.schema._parseAsync({ data: ctx.data, path: ctx.path, parent: ctx }).then((inner) => {
          if (inner.status === "aborted")
            return INVALID;
          if (inner.status === "dirty")
            status.dirty();
          return executeRefinement(inner.value).then(() => {
            return { status: status.value, value: inner.value };
          });
        });
      }
    }
    if (effect.type === "transform") {
      if (ctx.common.async === false) {
        const base = this._def.schema._parseSync({
          data: ctx.data,
          path: ctx.path,
          parent: ctx
        });
        if (!isValid(base))
          return INVALID;
        const result = effect.transform(base.value, checkCtx);
        if (result instanceof Promise) {
          throw new Error(`Asynchronous transform encountered during synchronous parse operation. Use .parseAsync instead.`);
        }
        return { status: status.value, value: result };
      } else {
        return this._def.schema._parseAsync({ data: ctx.data, path: ctx.path, parent: ctx }).then((base) => {
          if (!isValid(base))
            return INVALID;
          return Promise.resolve(effect.transform(base.value, checkCtx)).then((result) => ({
            status: status.value,
            value: result
          }));
        });
      }
    }
    util.assertNever(effect);
  }
};
ZodEffects.create = (schema, effect, params) => {
  return new ZodEffects({
    schema,
    typeName: ZodFirstPartyTypeKind.ZodEffects,
    effect,
    ...processCreateParams(params)
  });
};
ZodEffects.createWithPreprocess = (preprocess, schema, params) => {
  return new ZodEffects({
    schema,
    effect: { type: "preprocess", transform: preprocess },
    typeName: ZodFirstPartyTypeKind.ZodEffects,
    ...processCreateParams(params)
  });
};
var ZodOptional = class extends ZodType {
  _parse(input) {
    const parsedType = this._getType(input);
    if (parsedType === ZodParsedType.undefined) {
      return OK(void 0);
    }
    return this._def.innerType._parse(input);
  }
  unwrap() {
    return this._def.innerType;
  }
};
ZodOptional.create = (type, params) => {
  return new ZodOptional({
    innerType: type,
    typeName: ZodFirstPartyTypeKind.ZodOptional,
    ...processCreateParams(params)
  });
};
var ZodNullable = class extends ZodType {
  _parse(input) {
    const parsedType = this._getType(input);
    if (parsedType === ZodParsedType.null) {
      return OK(null);
    }
    return this._def.innerType._parse(input);
  }
  unwrap() {
    return this._def.innerType;
  }
};
ZodNullable.create = (type, params) => {
  return new ZodNullable({
    innerType: type,
    typeName: ZodFirstPartyTypeKind.ZodNullable,
    ...processCreateParams(params)
  });
};
var ZodDefault = class extends ZodType {
  _parse(input) {
    const { ctx } = this._processInputParams(input);
    let data = ctx.data;
    if (ctx.parsedType === ZodParsedType.undefined) {
      data = this._def.defaultValue();
    }
    return this._def.innerType._parse({
      data,
      path: ctx.path,
      parent: ctx
    });
  }
  removeDefault() {
    return this._def.innerType;
  }
};
ZodDefault.create = (type, params) => {
  return new ZodDefault({
    innerType: type,
    typeName: ZodFirstPartyTypeKind.ZodDefault,
    defaultValue: typeof params.default === "function" ? params.default : () => params.default,
    ...processCreateParams(params)
  });
};
var ZodCatch = class extends ZodType {
  _parse(input) {
    const { ctx } = this._processInputParams(input);
    const newCtx = {
      ...ctx,
      common: {
        ...ctx.common,
        issues: []
      }
    };
    const result = this._def.innerType._parse({
      data: newCtx.data,
      path: newCtx.path,
      parent: {
        ...newCtx
      }
    });
    if (isAsync(result)) {
      return result.then((result2) => {
        return {
          status: "valid",
          value: result2.status === "valid" ? result2.value : this._def.catchValue({
            get error() {
              return new ZodError(newCtx.common.issues);
            },
            input: newCtx.data
          })
        };
      });
    } else {
      return {
        status: "valid",
        value: result.status === "valid" ? result.value : this._def.catchValue({
          get error() {
            return new ZodError(newCtx.common.issues);
          },
          input: newCtx.data
        })
      };
    }
  }
  removeCatch() {
    return this._def.innerType;
  }
};
ZodCatch.create = (type, params) => {
  return new ZodCatch({
    innerType: type,
    typeName: ZodFirstPartyTypeKind.ZodCatch,
    catchValue: typeof params.catch === "function" ? params.catch : () => params.catch,
    ...processCreateParams(params)
  });
};
var ZodNaN = class extends ZodType {
  _parse(input) {
    const parsedType = this._getType(input);
    if (parsedType !== ZodParsedType.nan) {
      const ctx = this._getOrReturnCtx(input);
      addIssueToContext(ctx, {
        code: ZodIssueCode.invalid_type,
        expected: ZodParsedType.nan,
        received: ctx.parsedType
      });
      return INVALID;
    }
    return { status: "valid", value: input.data };
  }
};
ZodNaN.create = (params) => {
  return new ZodNaN({
    typeName: ZodFirstPartyTypeKind.ZodNaN,
    ...processCreateParams(params)
  });
};
var BRAND = Symbol("zod_brand");
var ZodBranded = class extends ZodType {
  _parse(input) {
    const { ctx } = this._processInputParams(input);
    const data = ctx.data;
    return this._def.type._parse({
      data,
      path: ctx.path,
      parent: ctx
    });
  }
  unwrap() {
    return this._def.type;
  }
};
var ZodPipeline = class _ZodPipeline extends ZodType {
  _parse(input) {
    const { status, ctx } = this._processInputParams(input);
    if (ctx.common.async) {
      const handleAsync = async () => {
        const inResult = await this._def.in._parseAsync({
          data: ctx.data,
          path: ctx.path,
          parent: ctx
        });
        if (inResult.status === "aborted")
          return INVALID;
        if (inResult.status === "dirty") {
          status.dirty();
          return DIRTY(inResult.value);
        } else {
          return this._def.out._parseAsync({
            data: inResult.value,
            path: ctx.path,
            parent: ctx
          });
        }
      };
      return handleAsync();
    } else {
      const inResult = this._def.in._parseSync({
        data: ctx.data,
        path: ctx.path,
        parent: ctx
      });
      if (inResult.status === "aborted")
        return INVALID;
      if (inResult.status === "dirty") {
        status.dirty();
        return {
          status: "dirty",
          value: inResult.value
        };
      } else {
        return this._def.out._parseSync({
          data: inResult.value,
          path: ctx.path,
          parent: ctx
        });
      }
    }
  }
  static create(a, b) {
    return new _ZodPipeline({
      in: a,
      out: b,
      typeName: ZodFirstPartyTypeKind.ZodPipeline
    });
  }
};
var ZodReadonly = class extends ZodType {
  _parse(input) {
    const result = this._def.innerType._parse(input);
    const freeze = (data) => {
      if (isValid(data)) {
        data.value = Object.freeze(data.value);
      }
      return data;
    };
    return isAsync(result) ? result.then((data) => freeze(data)) : freeze(result);
  }
  unwrap() {
    return this._def.innerType;
  }
};
ZodReadonly.create = (type, params) => {
  return new ZodReadonly({
    innerType: type,
    typeName: ZodFirstPartyTypeKind.ZodReadonly,
    ...processCreateParams(params)
  });
};
function cleanParams(params, data) {
  const p = typeof params === "function" ? params(data) : typeof params === "string" ? { message: params } : params;
  const p2 = typeof p === "string" ? { message: p } : p;
  return p2;
}
function custom(check, _params = {}, fatal) {
  if (check)
    return ZodAny.create().superRefine((data, ctx) => {
      const r = check(data);
      if (r instanceof Promise) {
        return r.then((r2) => {
          if (!r2) {
            const params = cleanParams(_params, data);
            const _fatal = params.fatal ?? fatal ?? true;
            ctx.addIssue({ code: "custom", ...params, fatal: _fatal });
          }
        });
      }
      if (!r) {
        const params = cleanParams(_params, data);
        const _fatal = params.fatal ?? fatal ?? true;
        ctx.addIssue({ code: "custom", ...params, fatal: _fatal });
      }
      return;
    });
  return ZodAny.create();
}
var late = {
  object: ZodObject.lazycreate
};
var ZodFirstPartyTypeKind;
(function(ZodFirstPartyTypeKind2) {
  ZodFirstPartyTypeKind2["ZodString"] = "ZodString";
  ZodFirstPartyTypeKind2["ZodNumber"] = "ZodNumber";
  ZodFirstPartyTypeKind2["ZodNaN"] = "ZodNaN";
  ZodFirstPartyTypeKind2["ZodBigInt"] = "ZodBigInt";
  ZodFirstPartyTypeKind2["ZodBoolean"] = "ZodBoolean";
  ZodFirstPartyTypeKind2["ZodDate"] = "ZodDate";
  ZodFirstPartyTypeKind2["ZodSymbol"] = "ZodSymbol";
  ZodFirstPartyTypeKind2["ZodUndefined"] = "ZodUndefined";
  ZodFirstPartyTypeKind2["ZodNull"] = "ZodNull";
  ZodFirstPartyTypeKind2["ZodAny"] = "ZodAny";
  ZodFirstPartyTypeKind2["ZodUnknown"] = "ZodUnknown";
  ZodFirstPartyTypeKind2["ZodNever"] = "ZodNever";
  ZodFirstPartyTypeKind2["ZodVoid"] = "ZodVoid";
  ZodFirstPartyTypeKind2["ZodArray"] = "ZodArray";
  ZodFirstPartyTypeKind2["ZodObject"] = "ZodObject";
  ZodFirstPartyTypeKind2["ZodUnion"] = "ZodUnion";
  ZodFirstPartyTypeKind2["ZodDiscriminatedUnion"] = "ZodDiscriminatedUnion";
  ZodFirstPartyTypeKind2["ZodIntersection"] = "ZodIntersection";
  ZodFirstPartyTypeKind2["ZodTuple"] = "ZodTuple";
  ZodFirstPartyTypeKind2["ZodRecord"] = "ZodRecord";
  ZodFirstPartyTypeKind2["ZodMap"] = "ZodMap";
  ZodFirstPartyTypeKind2["ZodSet"] = "ZodSet";
  ZodFirstPartyTypeKind2["ZodFunction"] = "ZodFunction";
  ZodFirstPartyTypeKind2["ZodLazy"] = "ZodLazy";
  ZodFirstPartyTypeKind2["ZodLiteral"] = "ZodLiteral";
  ZodFirstPartyTypeKind2["ZodEnum"] = "ZodEnum";
  ZodFirstPartyTypeKind2["ZodEffects"] = "ZodEffects";
  ZodFirstPartyTypeKind2["ZodNativeEnum"] = "ZodNativeEnum";
  ZodFirstPartyTypeKind2["ZodOptional"] = "ZodOptional";
  ZodFirstPartyTypeKind2["ZodNullable"] = "ZodNullable";
  ZodFirstPartyTypeKind2["ZodDefault"] = "ZodDefault";
  ZodFirstPartyTypeKind2["ZodCatch"] = "ZodCatch";
  ZodFirstPartyTypeKind2["ZodPromise"] = "ZodPromise";
  ZodFirstPartyTypeKind2["ZodBranded"] = "ZodBranded";
  ZodFirstPartyTypeKind2["ZodPipeline"] = "ZodPipeline";
  ZodFirstPartyTypeKind2["ZodReadonly"] = "ZodReadonly";
})(ZodFirstPartyTypeKind || (ZodFirstPartyTypeKind = {}));
var instanceOfType = (cls, params = {
  message: `Input not instance of ${cls.name}`
}) => custom((data) => data instanceof cls, params);
var stringType = ZodString.create;
var numberType = ZodNumber.create;
var nanType = ZodNaN.create;
var bigIntType = ZodBigInt.create;
var booleanType = ZodBoolean.create;
var dateType = ZodDate.create;
var symbolType = ZodSymbol.create;
var undefinedType = ZodUndefined.create;
var nullType = ZodNull.create;
var anyType = ZodAny.create;
var unknownType = ZodUnknown.create;
var neverType = ZodNever.create;
var voidType = ZodVoid.create;
var arrayType = ZodArray.create;
var objectType = ZodObject.create;
var strictObjectType = ZodObject.strictCreate;
var unionType = ZodUnion.create;
var discriminatedUnionType = ZodDiscriminatedUnion.create;
var intersectionType = ZodIntersection.create;
var tupleType = ZodTuple.create;
var recordType = ZodRecord.create;
var mapType = ZodMap.create;
var setType = ZodSet.create;
var functionType = ZodFunction.create;
var lazyType = ZodLazy.create;
var literalType = ZodLiteral.create;
var enumType = ZodEnum.create;
var nativeEnumType = ZodNativeEnum.create;
var promiseType = ZodPromise.create;
var effectsType = ZodEffects.create;
var optionalType = ZodOptional.create;
var nullableType = ZodNullable.create;
var preprocessType = ZodEffects.createWithPreprocess;
var pipelineType = ZodPipeline.create;
var ostring = () => stringType().optional();
var onumber = () => numberType().optional();
var oboolean = () => booleanType().optional();
var coerce = {
  string: ((arg) => ZodString.create({ ...arg, coerce: true })),
  number: ((arg) => ZodNumber.create({ ...arg, coerce: true })),
  boolean: ((arg) => ZodBoolean.create({
    ...arg,
    coerce: true
  })),
  bigint: ((arg) => ZodBigInt.create({ ...arg, coerce: true })),
  date: ((arg) => ZodDate.create({ ...arg, coerce: true }))
};
var NEVER = INVALID;

// dist/schemas/common.js
var surveyCodeSchema = external_exports.string().min(1).regex(/^\S(?:[\s\S]*\S)?$/, "Codes cannot contain leading or trailing whitespace.");
var jsonScalarSchema = external_exports.union([
  external_exports.string(),
  external_exports.number().finite(),
  external_exports.boolean()
]);
var jsonPrimitiveSchema = external_exports.union([
  jsonScalarSchema,
  external_exports.null()
]);
var jsonValueSchema = external_exports.lazy(() => external_exports.union([
  jsonPrimitiveSchema,
  external_exports.array(jsonValueSchema),
  external_exports.record(jsonValueSchema)
]));
var jsonObjectSchema = external_exports.record(jsonValueSchema);

// dist/schemas/grading.js
var surveyGradingSchema = external_exports.object({
  points: external_exports.number().finite().nonnegative(),
  correctAnswers: external_exports.array(jsonPrimitiveSchema).min(1),
  whenRight: external_exports.string().optional(),
  whenWrong: external_exports.string().optional(),
  generalFeedback: external_exports.string().optional()
}).strict();

// dist/schemas/conditions.js
var surveyConditionReferenceSchema = external_exports.object({
  fieldCode: surveyCodeSchema,
  responseItemCode: surveyCodeSchema.optional()
}).strict();
var surveyComparisonConditionSchema = external_exports.object({
  type: external_exports.literal("comparison"),
  responseReference: surveyConditionReferenceSchema,
  operator: external_exports.enum([
    "equals",
    "not-equals",
    "greater-than",
    "greater-than-or-equal",
    "less-than",
    "less-than-or-equal"
  ]),
  value: jsonPrimitiveSchema
}).strict();
var surveyAnsweredConditionSchema = external_exports.object({
  type: external_exports.enum(["answered", "not-answered"]),
  responseReference: surveyConditionReferenceSchema
}).strict();
var surveyPatternConditionSchema = external_exports.object({
  type: external_exports.literal("pattern-match"),
  responseReference: surveyConditionReferenceSchema,
  pattern: external_exports.string(),
  patternFlags: external_exports.string().regex(/^(?!.*(.).*\1)[ims]*$/).optional()
}).strict().superRefine((condition, context) => {
  try {
    new RegExp(condition.pattern, condition.patternFlags);
  } catch {
    context.addIssue({ code: external_exports.ZodIssueCode.custom, path: ["pattern"], message: "Invalid ECMAScript pattern." });
  }
});
var surveySelectionCountConditionSchema = external_exports.object({
  type: external_exports.literal("selection-count"),
  responseReference: surveyConditionReferenceSchema,
  /** Omit to count every response item; otherwise use exactly these items. */
  responseItemCodes: external_exports.array(surveyCodeSchema).min(1).optional(),
  operator: external_exports.enum([
    "equals",
    "not-equals",
    "greater-than",
    "greater-than-or-equal",
    "less-than",
    "less-than-or-equal"
  ]),
  value: external_exports.number().int().nonnegative()
}).strict();
var surveyAnsweredCountConditionSchema = surveySelectionCountConditionSchema.extend({
  type: external_exports.literal("answered-count")
}).strict();
var surveyNumericAggregateConditionSchema = surveySelectionCountConditionSchema.extend({
  type: external_exports.literal("numeric-aggregate"),
  aggregation: external_exports.enum(["sum", "min", "max"]),
  value: external_exports.number().finite()
}).strict();
var surveyConstantConditionSchema = external_exports.object({
  type: external_exports.literal("constant"),
  value: external_exports.boolean()
}).strict();
var surveyConditionSchema = external_exports.lazy(() => external_exports.union([
  surveyComparisonConditionSchema,
  surveyAnsweredConditionSchema,
  surveyPatternConditionSchema,
  surveySelectionCountConditionSchema,
  surveyAnsweredCountConditionSchema,
  surveyNumericAggregateConditionSchema,
  surveyConstantConditionSchema,
  external_exports.object({
    type: external_exports.enum(["all", "any"]),
    conditions: external_exports.array(surveyConditionSchema).min(1)
  }).strict(),
  external_exports.object({
    type: external_exports.literal("not"),
    condition: surveyConditionSchema
  }).strict()
]));
var surveyStructureVisibilitySchema = external_exports.object({
  condition: surveyConditionSchema
}).strict();

// dist/schemas/field-collections.js
var surveyStructureOptionSchema = external_exports.object({
  code: surveyCodeSchema,
  label: external_exports.string(),
  commentResponseKey: surveyCodeSchema.optional(),
  exclusive: external_exports.boolean().optional(),
  visibility: surveyStructureVisibilitySchema.optional(),
  order: external_exports.number().int().nonnegative().optional()
}).strict();
var surveyStructureSubquestionSchema = external_exports.object({
  id: external_exports.string().optional(),
  code: surveyCodeSchema,
  label: external_exports.string(),
  order: external_exports.number().int().nonnegative().optional()
}).strict();
var matrixItemSchema = surveyStructureOptionSchema.omit({ exclusive: true, commentResponseKey: true });
var surveyStructureBasicMatrixSchema = external_exports.object({
  mode: external_exports.enum(["single", "multiple", "text"]),
  rows: external_exports.array(matrixItemSchema.extend({
    visibility: surveyStructureVisibilitySchema.optional(),
    grading: surveyGradingSchema.optional(),
    /** When absent, inherit the matrix's required setting. */
    required: external_exports.boolean().optional()
  })),
  columns: external_exports.array(matrixItemSchema),
  cells: external_exports.array(external_exports.object({
    rowCode: surveyCodeSchema,
    columnCode: surveyCodeSchema,
    visibility: surveyStructureVisibilitySchema
  }).strict()).optional()
}).strict();
var surveyStructureNumberMatrixSchema = surveyStructureBasicMatrixSchema.extend({ mode: external_exports.literal("number") });
var surveyStructureDualMatrixSchema = surveyStructureBasicMatrixSchema.extend({
  mode: external_exports.literal("dual-single"),
  columns: external_exports.array(matrixItemSchema.extend({ options: external_exports.array(matrixItemSchema).min(1) })).length(2)
});
var surveyStructureMatrixSchema = external_exports.union([
  surveyStructureBasicMatrixSchema,
  surveyStructureNumberMatrixSchema,
  surveyStructureDualMatrixSchema
]);

// dist/schemas/rendering.js
var surveyStructureWidgetSchema = external_exports.enum([
  "text-input",
  "text-area",
  "date-picker",
  "checkbox",
  "slider",
  "radio-group",
  "button-group",
  "emoticon-slider",
  "dropdown",
  "toggle",
  "checkbox-group-with-comments",
  "gender-selector",
  "matrix-grid",
  "multiple-input-list",
  "rating",
  "numbered-radio-group",
  "ranking-list",
  "checkbox-group",
  "custom"
]);
var surveyRenderingInputTypeSchema = external_exports.enum([
  "text",
  "email",
  "number",
  "date",
  "datetime",
  "range",
  "password"
]);
var surveyRenderingInputModeSchema = external_exports.enum([
  "text",
  "numeric",
  "decimal",
  "tel",
  "email",
  "url",
  "search"
]);
var surveyRenderingDateOrderSchema = external_exports.enum(["date-time", "time-date"]);
var surveyStructureRenderingSchema = external_exports.object({
  widget: surveyStructureWidgetSchema.optional(),
  placeholder: external_exports.string().optional(),
  showLabel: external_exports.boolean().optional(),
  disabled: external_exports.boolean().optional(),
  /** Keep the field's value available to conditions without displaying an input. */
  hidden: external_exports.boolean().optional(),
  inputType: surveyRenderingInputTypeSchema.optional(),
  inputMode: surveyRenderingInputModeSchema.optional(),
  dateOrder: surveyRenderingDateOrderSchema.optional(),
  dateFormat: external_exports.enum(["dmy", "mdy", "ymd"]).optional(),
  dateDropdowns: external_exports.boolean().optional(),
  monthLabelStyle: external_exports.enum(["short", "long", "numeric"]).optional(),
  reverseYearOrder: external_exports.boolean().optional(),
  yearMin: external_exports.number().int().optional(),
  yearMax: external_exports.number().int().optional(),
  randomizationGroup: external_exports.string().min(1).optional(),
  searchable: external_exports.boolean().optional(),
  optionsLayout: external_exports.enum(["horizontal", "vertical"]).optional(),
  ratingIcon: external_exports.enum(["star", "heart", "thumb-up"]).optional(),
  scaleMinLabel: external_exports.string().optional(),
  scaleMaxLabel: external_exports.string().optional()
}).strict();

// dist/schemas/responses.js
var surveyStructureResponseEncodingSchema = external_exports.object({
  selectedValue: jsonScalarSchema,
  unselectedValue: jsonScalarSchema,
  selectedLabel: external_exports.string().min(1).optional(),
  unselectedLabel: external_exports.string().min(1).optional()
}).strict().refine(({ selectedValue, unselectedValue }) => selectedValue !== unselectedValue, { message: "selectedValue and unselectedValue must be different." });
var surveyStructureOtherResponseSchema = external_exports.object({
  code: surveyCodeSchema,
  label: external_exports.string().min(1),
  textResponseKey: surveyCodeSchema,
  commentResponseKey: surveyCodeSchema.optional(),
  /** Required only while the Other answer is active. */
  textRequired: external_exports.boolean().optional(),
  commentRequired: external_exports.boolean().optional()
}).strict();

// dist/schemas/validation.js
var dateBoundSchema = external_exports.string().regex(/^\d{4}-\d{2}-\d{2}$/).refine((value) => {
  const date = /* @__PURE__ */ new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}, "Use a valid ISO calendar date (YYYY-MM-DD).");
var surveyStructureResponseValidationSchema = external_exports.object({
  min: external_exports.number().finite().optional(),
  max: external_exports.number().finite().optional(),
  dateMin: dateBoundSchema.optional(),
  dateMax: dateBoundSchema.optional(),
  /** Omission keeps existing blocking behavior; warnings never invalidate an answer. */
  rangeBehavior: external_exports.enum(["warning", "error"]).optional(),
  minLength: external_exports.number().int().nonnegative().optional(),
  maxLength: external_exports.number().int().nonnegative().optional(),
  minSelections: external_exports.number().int().nonnegative().optional(),
  maxSelections: external_exports.number().int().nonnegative().optional(),
  // Single matrices count answered rows; text matrices count nonempty cells.
  minAnswers: external_exports.number().int().nonnegative().optional(),
  maxAnswers: external_exports.number().int().nonnegative().optional(),
  integer: external_exports.boolean().optional(),
  /** Check numeric syntax while keeping the answer's exact text. */
  numericText: external_exports.boolean().optional(),
  /** Fixed limits for each numeric box and for the total of a multiple-input field. */
  itemMin: external_exports.number().finite().optional(),
  itemMax: external_exports.number().finite().optional(),
  sumMin: external_exports.number().finite().optional(),
  sumMax: external_exports.number().finite().optional(),
  sumEquals: external_exports.number().finite().optional(),
  itemMinReference: external_exports.string().min(1).optional(),
  itemMaxReference: external_exports.string().min(1).optional(),
  sumMinReference: external_exports.string().min(1).optional(),
  sumMaxReference: external_exports.string().min(1).optional(),
  sumEqualsReference: external_exports.string().min(1).optional(),
  sumAllowsMissing: external_exports.boolean().optional(),
  /** Regular expression source, evaluated exactly as written. */
  responseFormatPattern: external_exports.string().optional(),
  patternFlags: external_exports.string().regex(/^(?!.*(.).*\1)[ims]*$/).optional(),
  messages: external_exports.record(external_exports.string()).optional()
}).strict().superRefine((validation, context) => {
  if (validation.dateMin !== void 0 && validation.dateMax !== void 0 && validation.dateMin > validation.dateMax) {
    context.addIssue({ code: external_exports.ZodIssueCode.custom, path: ["dateMax"], message: "dateMax must be on or after dateMin." });
  }
  if (validation.responseFormatPattern !== void 0) {
    try {
      new RegExp(validation.responseFormatPattern, validation.patternFlags);
    } catch {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: ["responseFormatPattern"],
        message: "responseFormatPattern must be valid ECMAScript regular expression source without flags.",
        params: { reason: "invalid-validation-pattern" }
      });
    }
  }
  if (validation.responseFormatPattern === void 0 && validation.patternFlags !== void 0) {
    context.addIssue({ code: external_exports.ZodIssueCode.custom, path: ["responseFormatPattern"], message: "Pattern options require a pattern." });
  }
  for (const rule of ["itemMin", "itemMax", "sumMin", "sumMax", "sumEquals"]) {
    if (validation[rule] !== void 0 && validation[`${rule}Reference`] !== void 0) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [`${rule}Reference`],
        message: `Use a fixed ${rule} or a reference, not both.`
      });
    }
  }
  const orderedPairs = [
    [validation.min, validation.max, "min", "max"],
    [validation.minLength, validation.maxLength, "minLength", "maxLength"],
    [validation.minSelections, validation.maxSelections, "minSelections", "maxSelections"],
    [validation.minAnswers, validation.maxAnswers, "minAnswers", "maxAnswers"],
    [validation.itemMin, validation.itemMax, "itemMin", "itemMax"],
    [validation.sumMin, validation.sumMax, "sumMin", "sumMax"]
  ];
  orderedPairs.forEach(([minimum, maximum, minimumName, maximumName]) => {
    if (minimum !== void 0 && maximum !== void 0 && minimum > maximum) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [maximumName],
        message: `${maximumName} must be greater than or equal to ${minimumName}.`
      });
    }
  });
  if (validation.sumEquals !== void 0 && (validation.sumMin !== void 0 && validation.sumEquals < validation.sumMin || validation.sumMax !== void 0 && validation.sumEquals > validation.sumMax)) {
    context.addIssue({ code: external_exports.ZodIssueCode.custom, path: ["sumEquals"], message: "sumEquals must satisfy the sum bounds." });
  }
});

// dist/schemas/source/common.js
var surveyPlatformIdentifierSchema = external_exports.string().regex(/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/, "platform must be a lowercase kebab-case identifier.");

// dist/schemas/source/limesurvey.js
var limeSurveyNativeValidationSchema = external_exports.object({
  minimumNumericValueExpression: external_exports.string().optional(),
  maximumNumericValueExpression: external_exports.string().optional(),
  minimumAnswerExpression: external_exports.string().optional(),
  maximumAnswerExpression: external_exports.string().optional(),
  minimumAnswersExpression: external_exports.string().optional(),
  maximumAnswersExpression: external_exports.string().optional(),
  questionValidationExpression: external_exports.string().optional(),
  subquestionValidationExpression: external_exports.string().optional(),
  minimumCellValueExpression: external_exports.string().optional(),
  maximumCellValueExpression: external_exports.string().optional(),
  cellStepExpression: external_exports.string().optional(),
  minimumDateExpression: external_exports.string().optional(),
  maximumDateExpression: external_exports.string().optional(),
  maximumCharactersExpression: external_exports.string().optional(),
  maximumRankingItemsExpression: external_exports.string().optional(),
  regularExpression: external_exports.string().optional(),
  minimumNumericAnswerValueExpression: external_exports.string().optional(),
  maximumNumericAnswerValueExpression: external_exports.string().optional()
}).strict();
var limeSurveyQuestionOriginDetailsSchema = external_exports.object({
  type: external_exports.literal("limesurvey-question"),
  version: external_exports.literal("1.0.0"),
  questionRelevanceExpression: external_exports.string().optional(),
  questionAndGroupRelevanceExpression: external_exports.string().optional(),
  dateTimeFormat: external_exports.string().optional(),
  nativeValidation: limeSurveyNativeValidationSchema.optional(),
  unconvertedAttributes: external_exports.record(jsonPrimitiveSchema).optional()
}).strict();
var limeSurveyGroupOriginDetailsSchema = external_exports.object({
  type: external_exports.literal("limesurvey-group"),
  version: external_exports.literal("1.0.0"),
  groupRelevanceExpression: external_exports.string().optional()
}).strict();
var limeSurveyOriginDetailsSchema = external_exports.object({
  type: external_exports.literal("limesurvey-survey"),
  version: external_exports.literal("1.0.0"),
  databaseSchemaVersion: external_exports.string().optional()
}).strict();

// dist/schemas/source/redcap.js
var redCapQuestionOriginDetailsSchema = external_exports.object({
  type: external_exports.literal("redcap-question"),
  version: external_exports.literal("1.0.0"),
  identifier: external_exports.boolean().optional(),
  customAlignment: external_exports.string().optional(),
  sectionHeader: external_exports.string().optional(),
  requiredField: external_exports.string().optional(),
  validationType: external_exports.string().optional(),
  validationMin: external_exports.string().optional(),
  validationMax: external_exports.string().optional(),
  branchingLogic: external_exports.string().optional(),
  questionNumber: external_exports.string().optional(),
  fieldAnnotation: external_exports.string().optional(),
  nativeMetadata: external_exports.record(external_exports.string()).optional()
}).strict();
var redCapOriginDetailsSchema = external_exports.object({
  type: external_exports.literal("redcap-survey"),
  version: external_exports.literal("1.0.0"),
  /** Import target, not the missing original survey-enabled setting. */
  targetCollectionMode: external_exports.enum(["survey", "data-entry", "unknown"]).optional()
}).strict();

// dist/schemas/source/source.js
var surveyStructureFieldOriginDetailsSchema = external_exports.discriminatedUnion("type", [
  limeSurveyQuestionOriginDetailsSchema,
  redCapQuestionOriginDetailsSchema
]);
var surveyStructureFieldSourceSchema = external_exports.object({
  platform: surveyPlatformIdentifierSchema,
  surveyId: external_exports.string().optional(),
  groupId: external_exports.string().optional(),
  questionId: external_exports.string().optional(),
  nativeType: external_exports.string().optional(),
  /** Source column names; omit responseItemCode for the field's own scalar response. */
  responseAliases: external_exports.array(external_exports.object({ responseItemCode: external_exports.string().min(1).optional(), aliases: external_exports.array(external_exports.string().min(1)).min(1) }).strict()).optional(),
  originDetails: external_exports.array(surveyStructureFieldOriginDetailsSchema).optional()
}).strict();
var surveyStructureGroupOriginDetailsSchema = external_exports.discriminatedUnion("type", [
  limeSurveyGroupOriginDetailsSchema
]);
var surveyStructureGroupSourceSchema = external_exports.object({
  platform: surveyPlatformIdentifierSchema,
  groupId: external_exports.string().optional(),
  originDetails: external_exports.array(surveyStructureGroupOriginDetailsSchema).optional()
}).strict();
var surveyStructureOriginDetailsSchema = external_exports.discriminatedUnion("type", [
  limeSurveyOriginDetailsSchema,
  redCapOriginDetailsSchema
]);
var surveyStructureSourceSchema = external_exports.object({
  platform: surveyPlatformIdentifierSchema,
  format: external_exports.string().optional(),
  version: external_exports.string().optional(),
  importedAt: external_exports.string().datetime({ offset: true }).optional(),
  originDetails: external_exports.array(surveyStructureOriginDetailsSchema).optional()
}).strict();

// dist/schemas/groups.js
var surveyStructureGroupSchema = external_exports.object({
  id: external_exports.string().min(1),
  title: external_exports.string().optional(),
  description: external_exports.string().optional(),
  order: external_exports.number().int().nonnegative(),
  randomizationGroup: external_exports.string().min(1).optional(),
  visibility: surveyStructureVisibilitySchema.optional(),
  source: surveyStructureGroupSourceSchema.optional(),
  /** First matching rule controls where Next/Submit goes after this group. */
  navigation: external_exports.array(external_exports.object({
    condition: surveyConditionSchema,
    destination: external_exports.union([
      external_exports.object({ action: external_exports.enum(["next", "end", "start"]) }).strict(),
      external_exports.object({ groupId: external_exports.string().min(1) }).strict()
    ])
  }).strict()).optional()
}).strict();

// dist/schemas/settings.js
var surveyStructureSettingsSchema = external_exports.object({
  layout: external_exports.enum(["all", "group", "question"]).optional(),
  showWelcome: external_exports.boolean().optional(),
  showProgress: external_exports.boolean().optional(),
  allowPrevious: external_exports.boolean().optional(),
  showGroupName: external_exports.boolean().optional(),
  showGroupDescription: external_exports.boolean().optional(),
  questionIndex: external_exports.enum(["inherit", "disabled", "incremental", "full"]).optional(),
  navigationDelay: external_exports.number().nonnegative().optional(),
  welcomeText: external_exports.string().optional(),
  endText: external_exports.string().optional(),
  policyNotice: external_exports.string().optional()
}).strict();

// dist/month-day.js
function monthDayCount(month) {
  return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1] ?? 0;
}
function isMonthDay(value) {
  if (typeof value !== "string" || !/^\d{2}-\d{2}$/.test(value))
    return false;
  const [month, day] = value.split("-").map(Number);
  return month >= 1 && month <= 12 && day >= 1 && day <= monthDayCount(month);
}

// dist/number-character-length.js
function numberCharacterLength(value) {
  const text = String(value);
  if (!text.includes("e"))
    return text.length;
  const [coefficient, exponent] = text.split("e");
  const sign = coefficient.startsWith("-") ? 1 : 0;
  const [whole, fraction = ""] = coefficient.slice(sign).split(".");
  const digits = whole.length + fraction.length;
  const point = whole.length + Number(exponent);
  return sign + (point <= 0 ? 2 - point + digits : point >= digits ? point : digits + 1);
}

// dist/numeric-text.js
function isNumericText(value) {
  const trimmed = value.replace(/^[ \t\n\r\f\v]+|[ \t\n\r\f\v]+$/g, "");
  return /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(trimmed) && Number.isFinite(Number(trimmed));
}

// dist/validation-pattern.js
function validationPatternSource(rules) {
  return rules.responseFormatPattern ?? "";
}

// dist/schemas/field-invariants.js
var FIELD_WIDGET_COMPATIBILITY = {
  "short-text": ["text-input"],
  "long-text": ["text-area"],
  number: ["text-input"],
  date: ["date-picker"],
  "yes-no": ["radio-group", "button-group", "dropdown"],
  gender: ["gender-selector", "radio-group", "button-group", "dropdown"],
  "single-choice": ["radio-group", "button-group", "rating", "emoticon-slider", "dropdown", "numbered-radio-group"],
  "list-with-comment": ["dropdown"],
  "multiple-choice": ["dropdown", "checkbox-group", "checkbox-group-with-comments"],
  "multiple-choice-with-comments": ["checkbox-group-with-comments"],
  matrix: ["matrix-grid"],
  "multiple-input": ["multiple-input-list"],
  ranking: ["ranking-list"],
  display: ["text-input"],
  boolean: ["checkbox", "toggle"],
  range: ["slider", "rating"],
  custom: ["custom"]
};
function validateFieldRules(field, context) {
  if (field.type === "range" && field.responseValueType === "text") {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["responseValueType"],
      message: "A range control cannot preserve numeric input as text."
    });
  }
  const widget = field.rendering?.widget;
  if (widget && !FIELD_WIDGET_COMPATIBILITY[field.type].includes(widget)) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["rendering", "widget"],
      message: `Widget "${widget}" is not compatible with field type "${field.type}".`,
      params: {
        reason: "widget-not-compatible-with-field-type",
        fieldCode: field.code,
        semanticFieldType: field.type,
        widget,
        allowedWidgets: FIELD_WIDGET_COMPATIBILITY[field.type]
      }
    });
  }
  if ("commentResponseKey" in field && field.commentResponseKey && field.type !== "list-with-comment") {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["commentResponseKey"],
      message: "commentResponseKey requires a list-with-comment field."
    });
  }
  if ("options" in field && field.type !== "multiple-choice-with-comments" && field.options.some((option) => option.commentResponseKey)) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["options"],
      message: "Option commentResponseKey requires multiple-choice-with-comments."
    });
  }
  if ("options" in field && field.options.some((option) => option.exclusive) && !["multiple-choice", "multiple-choice-with-comments"].includes(field.type)) {
    context.addIssue({ code: external_exports.ZodIssueCode.custom, path: ["options"], message: "Exclusive options require a checkbox question." });
  }
  if ("options" in field && field.options.some((option) => option.visibility) && !["multiple-choice", "multiple-choice-with-comments"].includes(field.type)) {
    context.addIssue({ code: external_exports.ZodIssueCode.custom, path: ["options"], message: "Option visibility is supported for checkbox questions." });
  }
  if (field.rendering?.widget === "rating" && field.type === "range" && (field.responseValidation?.min !== 1 || !Number.isInteger(field.responseValidation?.max) || field.responseValidation.max > 10 || field.responseValidation.max < 1 || field.responseValidation?.integer !== true)) {
    context.addIssue({ code: external_exports.ZodIssueCode.custom, path: ["rendering"], message: "Rating requires integer values from 1 to a maximum of 10." });
  }
  if (field.grading && !["short-text", "long-text", "number", "range", "yes-no", "gender", "single-choice", "list-with-comment", "multiple-choice", "multiple-choice-with-comments", "boolean", "date"].includes(field.type)) {
    context.addIssue({ code: external_exports.ZodIssueCode.custom, path: ["grading"], message: "Automatic grading requires a scalar or checkbox question; matrices use grading per row." });
  }
  const validation = field.responseValidation;
  if (validation) {
    if ((validation.dateMin !== void 0 || validation.dateMax !== void 0) && !(field.type === "date" && ["date", "date-time"].includes(field.dateValueType))) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: ["responseValidation"],
        message: `Field "${field.code}" can only declare dateMin/dateMax for a calendar date or date-time.`
      });
    }
    if (validation.rangeBehavior !== void 0 && validation.min === void 0 && validation.max === void 0 && validation.dateMin === void 0 && validation.dateMax === void 0) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: ["responseValidation", "rangeBehavior"],
        message: "rangeBehavior requires a numeric or date bound."
      });
    }
    const numericRules = validation.min !== void 0 || validation.max !== void 0 || validation.integer !== void 0 && field.type !== "multiple-input";
    if (validation.integer !== void 0 && field.type === "multiple-input" && validation.numericText !== true) {
      addRuleIssue(context, `Field "${field.code}" requires numericText for integer multiple inputs.`, field, ["integer"]);
    }
    const multiNumericRules = validation.itemMin !== void 0 || validation.itemMax !== void 0 || validation.sumMin !== void 0 || validation.sumMax !== void 0 || validation.sumEquals !== void 0 || validation.itemMinReference !== void 0 || validation.itemMaxReference !== void 0 || validation.sumMinReference !== void 0 || validation.sumMaxReference !== void 0 || validation.sumEqualsReference !== void 0 || validation.sumAllowsMissing !== void 0;
    if (multiNumericRules && (field.type !== "multiple-input" || validation.numericText !== true)) {
      addRuleIssue(context, `Field "${field.code}" can only declare multiple numeric rules for numeric multiple inputs.`, field, ["itemMin", "itemMax", "sumMin", "sumMax", "sumEquals", "sumAllowsMissing"]);
    }
    const textRules = validation.minLength !== void 0 || validation.responseFormatPattern !== void 0;
    const textField = field.type === "short-text" || field.type === "long-text";
    const numericTextField = field.type === "number" && field.responseValueType === "text";
    if (validation.numericText !== void 0 && !textField && field.type !== "multiple-input" && !(field.type === "matrix" && field.matrix.mode === "text")) {
      addRuleIssue(context, `Field "${field.code}" cannot require numeric text for this response type.`, field, ["numericText"]);
    }
    if (validation.maxLength !== void 0 && !textField && field.type !== "number" && field.type !== "multiple-input" && !(field.type === "matrix" && field.matrix.mode === "text")) {
      addRuleIssue(context, `Field "${field.code}" cannot declare maxLength for this response type.`, field, ["maxLength"]);
    }
    const selectionRules = validation.minSelections !== void 0 || validation.maxSelections !== void 0;
    const answerRules = validation.minAnswers !== void 0 || validation.maxAnswers !== void 0;
    if (answerRules && !(field.type === "matrix" && ["single", "text"].includes(field.matrix.mode))) {
      addRuleIssue(context, `Field "${field.code}" cannot declare minAnswers or maxAnswers. These rules count answered rows in single matrices or cells in text matrices.`, field, ["minAnswers", "maxAnswers"]);
    }
    if (numericRules && field.type !== "number" && field.type !== "range" && !(field.type === "matrix" && field.matrix.mode === "number")) {
      addRuleIssue(context, `Field "${field.code}" has type "${field.type}", so it cannot declare numeric min, max or integer rules.`, field, ["min", "max", "integer"]);
    }
    if (textRules && !textField && !(numericTextField && validation.minLength === void 0)) {
      addRuleIssue(context, `Field "${field.code}" has type "${field.type}", so it cannot declare minLength or pattern rules.`, field, ["minLength", "responseFormatPattern"]);
    }
    if (selectionRules && ![
      "multiple-choice",
      "multiple-choice-with-comments",
      "ranking"
    ].includes(field.type)) {
      addRuleIssue(context, `Field "${field.code}" has type "${field.type}", so it cannot declare minSelections or maxSelections. These rules apply only to fields that allow multiple selections.`, field, ["minSelections", "maxSelections"]);
    }
  }
  if ("other" in field && field.other && field.options.some((option) => option.code === field.other?.code)) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["other", "code"],
      message: "The Other response must use a code distinct from ordinary options.",
      params: { reason: "other-option-code-collision", fieldCode: field.code }
    });
  }
  if ("other" in field && field.other?.commentResponseKey && field.type !== "multiple-choice-with-comments") {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["other", "commentResponseKey"],
      message: "commentResponseKey applies only to multiple-choice-with-comments fields.",
      params: {
        reason: "other-comment-key-incompatible-field-type",
        fieldCode: field.code,
        semanticFieldType: field.type
      }
    });
  }
  if ("other" in field && field.other?.commentRequired !== void 0 && (field.type !== "multiple-choice-with-comments" || !field.other.commentResponseKey)) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["other", "commentRequired"],
      message: "commentRequired requires a multiple-choice-with-comments field and commentResponseKey."
    });
  }
  if ("other" in field && field.other && ["yes-no", "gender", "ranking"].includes(field.type)) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["other"],
      message: `Field type "${field.type}" cannot declare an Other response.`,
      params: {
        reason: "other-response-incompatible-field-type",
        fieldCode: field.code,
        semanticFieldType: field.type
      }
    });
  }
  validateResponseEncoding(field, context);
  validateDefaultValue(field, context);
  if (field.type === "date" && field.defaultValue !== void 0 && !isDateDefault(field.dateValueType, field.defaultValue)) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["defaultValue"],
      message: `defaultValue does not match dateValueType ${field.dateValueType}.`,
      params: {
        reason: "date-default-value-format-mismatch",
        fieldCode: field.code,
        dateValueType: field.dateValueType
      }
    });
  }
}
function validateResponseEncoding(field, context) {
  const encoding = field.responseEncoding;
  if (!encoding)
    return;
  const supported = field.type === "multiple-choice" || field.type === "multiple-choice-with-comments" || field.type === "boolean" || field.type === "matrix" && field.matrix.mode === "multiple";
  if (!supported) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["responseEncoding"],
      message: `Field type "${field.type}" does not produce selected/unselected response values.`,
      params: {
        reason: "response-encoding-incompatible-field-type",
        fieldCode: field.code,
        semanticFieldType: field.type
      }
    });
  }
  if (typeof encoding.selectedValue !== typeof encoding.unselectedValue) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["responseEncoding"],
      message: "selectedValue and unselectedValue must use the same JSON primitive type.",
      params: {
        reason: "response-encoding-value-type-mismatch",
        fieldCode: field.code
      }
    });
  }
  if (encoding.selectedLabel === void 0 !== (encoding.unselectedLabel === void 0)) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: ["responseEncoding"],
      message: "selectedLabel and unselectedLabel must be provided together or both omitted.",
      params: {
        reason: "response-encoding-label-pair-incomplete",
        fieldCode: field.code
      }
    });
  }
}
function validateDefaultValue(field, context) {
  if (!("defaultValue" in field) || field.defaultValue === void 0)
    return;
  const rules = field.responseValidation;
  const invalidDefault = (path = []) => context.addIssue({
    code: external_exports.ZodIssueCode.custom,
    path: ["defaultValue", ...path],
    message: "defaultValue violates its field validation.",
    params: { reason: "default-value-validation-mismatch", fieldCode: field.code }
  });
  const invalidNumber = (value, checkCharacterLength = true) => rules?.rangeBehavior !== "warning" && (rules?.min !== void 0 && value < rules.min || rules?.max !== void 0 && value > rules.max) || rules?.integer === true && !Number.isInteger(value) || checkCharacterLength && rules?.maxLength !== void 0 && numberCharacterLength(value) > rules.maxLength;
  if (field.type === "number" || field.type === "range") {
    const textMode = field.type === "number" && field.responseValueType === "text";
    if (textMode) {
      const value = field.defaultValue;
      let matchesPattern = true;
      if (typeof value === "string" && rules?.responseFormatPattern !== void 0) {
        try {
          matchesPattern = new RegExp(validationPatternSource(rules), rules.patternFlags).test(value);
        } catch {
        }
      }
      if (typeof value !== "string" || !isNumericText(value) || !Number.isFinite(Number(value.trim())) || invalidNumber(Number(value.trim()), false) || rules?.maxLength !== void 0 && value.length > rules.maxLength || !matchesPattern)
        invalidDefault();
    } else if (typeof field.defaultValue !== "number" || invalidNumber(field.defaultValue))
      invalidDefault();
  }
  if (field.type === "date" && rules?.rangeBehavior !== "warning" && (rules?.dateMin !== void 0 && field.defaultValue.slice(0, 10) < rules.dateMin || rules?.dateMax !== void 0 && field.defaultValue.slice(0, 10) > rules.dateMax))
    invalidDefault();
  if (field.type === "short-text" || field.type === "long-text") {
    if (rules?.minLength !== void 0 && field.defaultValue.length < rules.minLength || rules?.maxLength !== void 0 && field.defaultValue.length > rules.maxLength)
      invalidDefault();
    if (rules?.responseFormatPattern !== void 0) {
      let pattern;
      try {
        pattern = new RegExp(validationPatternSource(rules), rules.patternFlags);
      } catch {
      }
      if (pattern && !pattern.test(field.defaultValue))
        invalidDefault();
    }
  }
  if ("options" in field) {
    const allowed = new Set(field.options.map((option) => option.code));
    if ("other" in field && field.other)
      allowed.add(field.other.code);
    const defaults = Array.isArray(field.defaultValue) ? field.defaultValue : [field.defaultValue];
    defaults.forEach((code, index) => {
      if (!allowed.has(code))
        addUnknownDefault(context, field, Array.isArray(field.defaultValue) ? [index] : [], code);
    });
    if (Array.isArray(field.defaultValue)) {
      if (rules?.minSelections !== void 0 && field.defaultValue.length < rules.minSelections || rules?.maxSelections !== void 0 && field.defaultValue.length > rules.maxSelections)
        invalidDefault();
      const duplicate = firstDuplicate(field.defaultValue);
      if (duplicate) {
        context.addIssue({
          code: external_exports.ZodIssueCode.custom,
          path: ["defaultValue"],
          message: `defaultValue repeats option code "${duplicate}".`,
          params: { reason: "duplicate-default-option-code", fieldCode: field.code, optionCode: duplicate }
        });
      }
      if (field.type === "ranking" && (field.defaultValue.length !== field.options.length || field.options.some((option) => !field.defaultValue?.includes(option.code)))) {
        context.addIssue({
          code: external_exports.ZodIssueCode.custom,
          path: ["defaultValue"],
          message: "A ranking defaultValue must contain every declared option exactly once.",
          params: { reason: "ranking-default-not-a-complete-order", fieldCode: field.code }
        });
      }
    }
    return;
  }
  if (field.type === "multiple-input") {
    validateObjectKeys(field.defaultValue, new Set(field.subquestions.map((item) => item.code)), field, context);
    Object.entries(field.defaultValue).forEach(([code, value]) => {
      if (rules?.maxLength !== void 0 && typeof value === "string" && value.length > rules.maxLength)
        invalidDefault([code]);
    });
    return;
  }
  if (field.type !== "matrix")
    return;
  const rows = new Set(field.matrix.rows.map((row) => row.code));
  const columns = new Set(field.matrix.columns.map((column) => column.code));
  Object.entries(field.defaultValue).forEach(([rowCode, rowValue]) => {
    if (!rows.has(rowCode))
      addUnknownDefault(context, field, [rowCode], rowCode, "matrix row");
    if (field.matrix.mode === "single") {
      if (!columns.has(rowValue))
        addUnknownDefault(context, field, [rowCode], rowValue, "matrix column");
      return;
    }
    Object.keys(rowValue).forEach((columnCode) => {
      if (!columns.has(columnCode))
        addUnknownDefault(context, field, [rowCode, columnCode], columnCode, "matrix column");
      const value = rowValue[columnCode];
      if (field.matrix.mode === "text" && typeof value === "string" && rules?.maxLength !== void 0 && value.length > rules.maxLength)
        invalidDefault([rowCode, columnCode]);
      if (field.matrix.mode === "dual-single") {
        const scale = field.matrix.columns.find((column) => column.code === columnCode);
        if (scale && !scale.options.some((option) => option.code === value)) {
          addUnknownDefault(context, field, [rowCode, columnCode], value, "scale option");
        }
      }
      if (field.matrix.mode === "number" && typeof value === "number") {
        if (invalidNumber(value))
          invalidDefault([rowCode, columnCode]);
      }
    });
  });
}
function validateObjectKeys(value, allowed, field, context) {
  Object.keys(value).forEach((key) => {
    if (!allowed.has(key))
      addUnknownDefault(context, field, [key], key, "subquestion");
  });
}
function addUnknownDefault(context, field, suffix, value, item = "option") {
  context.addIssue({
    code: external_exports.ZodIssueCode.custom,
    path: ["defaultValue", ...suffix],
    message: `defaultValue references unknown ${item} code "${String(value)}" in field "${field.code}".`,
    params: {
      reason: "default-value-reference-missing",
      fieldCode: field.code,
      responseItemCode: String(value),
      itemType: item
    }
  });
}
function firstDuplicate(values) {
  const seen = /* @__PURE__ */ new Set();
  for (const value of values) {
    if (seen.has(value))
      return value;
    seen.add(value);
  }
  return void 0;
}
function addRuleIssue(context, message, field, rules) {
  context.addIssue({
    code: external_exports.ZodIssueCode.custom,
    path: ["responseValidation"],
    message,
    params: field && rules ? {
      reason: "validation-rule-not-applicable",
      fieldCode: field.code,
      semanticFieldType: field.type,
      rules
    } : void 0
  });
}
function isDateDefault(type, value) {
  if (type === "month-day")
    return isMonthDay(value);
  const patterns = {
    date: /^\d{4}-\d{2}-\d{2}$/,
    "month-year": /^\d{4}-\d{2}$/,
    "date-time": /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?$/,
    time: /^\d{2}:\d{2}(?::\d{2})?$/,
    year: /^\d{4}$/
  };
  if (!patterns[type].test(value))
    return false;
  if (type === "year")
    return Number(value) >= 1;
  if (type !== "time") {
    const [year, month, day = 1] = value.split("T")[0].split("-").map(Number);
    if (year < 1 || month < 1 || month > 12)
      return false;
    const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    const days = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if (day < 1 || day > days[month - 1])
      return false;
  }
  if (type === "time" || type === "date-time") {
    const time = type === "time" ? value : value.split("T")[1];
    const [hour, minute, second = "0"] = time.replace(/Z|[+-].*$/, "").split(":");
    if (Number(hour) > 23 || Number(minute) > 59 || Number(second) >= 60)
      return false;
    const offset = time.match(/[+-](\d{2}):(\d{2})$/);
    if (offset && (Number(offset[1]) > 23 || Number(offset[2]) > 59))
      return false;
  }
  return true;
}

// dist/schemas/field.js
var surveyStructureFieldTypeSchema = external_exports.enum([
  "short-text",
  "long-text",
  "number",
  "date",
  "yes-no",
  "gender",
  "single-choice",
  "list-with-comment",
  "multiple-choice",
  "multiple-choice-with-comments",
  "matrix",
  "multiple-input",
  "ranking",
  "display",
  "boolean",
  "range",
  "custom"
]);
var surveyDateValueTypeSchema = external_exports.enum([
  "date",
  "month-year",
  "month-day",
  "date-time",
  "time",
  "year"
]);
var surveyStructureFieldBaseSchema = external_exports.object({
  id: external_exports.string().min(1),
  code: surveyCodeSchema,
  type: surveyStructureFieldTypeSchema,
  label: external_exports.string(),
  groupId: external_exports.string().optional(),
  parentId: external_exports.string().optional(),
  help: external_exports.string().optional(),
  images: external_exports.array(external_exports.object({ url: external_exports.string().url(), alt: external_exports.string() }).strict()).optional(),
  required: external_exports.boolean().optional(),
  grading: surveyGradingSchema.optional(),
  order: external_exports.number().int().nonnegative().optional(),
  responseValidation: surveyStructureResponseValidationSchema.optional(),
  visibility: surveyStructureVisibilitySchema.optional(),
  rendering: surveyStructureRenderingSchema.optional(),
  responseEncoding: surveyStructureResponseEncodingSchema.optional(),
  source: surveyStructureFieldSourceSchema.optional()
}).strict();
var surveyStructureSingleChoiceFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.enum(["yes-no", "gender", "single-choice", "list-with-comment"]),
  options: external_exports.array(surveyStructureOptionSchema),
  commentResponseKey: surveyCodeSchema.optional(),
  defaultValue: external_exports.string().optional(),
  other: surveyStructureOtherResponseSchema.optional()
});
var surveyStructureMultipleChoiceFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.enum(["multiple-choice", "multiple-choice-with-comments", "ranking"]),
  options: external_exports.array(surveyStructureOptionSchema),
  defaultValue: external_exports.array(external_exports.string()).optional(),
  other: surveyStructureOtherResponseSchema.optional()
});
var surveyStructureSingleMatrixFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("matrix"),
  matrix: surveyStructureBasicMatrixSchema.extend({ mode: external_exports.literal("single") }),
  defaultValue: external_exports.record(external_exports.string()).optional()
});
var surveyStructureMultipleMatrixFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("matrix"),
  matrix: surveyStructureBasicMatrixSchema.extend({ mode: external_exports.literal("multiple") }),
  defaultValue: external_exports.record(external_exports.record(external_exports.boolean())).optional()
});
var surveyStructureTextMatrixFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("matrix"),
  matrix: surveyStructureBasicMatrixSchema.extend({ mode: external_exports.literal("text") }),
  defaultValue: external_exports.record(external_exports.record(external_exports.string())).optional()
});
var surveyStructureNumberMatrixFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("matrix"),
  matrix: surveyStructureNumberMatrixSchema,
  defaultValue: external_exports.record(external_exports.record(external_exports.number().finite())).optional()
});
var surveyStructureDualMatrixFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("matrix"),
  matrix: surveyStructureDualMatrixSchema,
  defaultValue: external_exports.record(external_exports.record(external_exports.string())).optional()
});
var surveyStructureMultipleInputFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("multiple-input"),
  subquestions: external_exports.array(surveyStructureSubquestionSchema),
  defaultValue: external_exports.record(jsonScalarSchema).optional()
});
var surveyStructureTextFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.enum(["short-text", "long-text"]),
  defaultValue: external_exports.string().optional()
});
var surveyStructureNumericFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.enum(["number", "range"]),
  /** Preserve the spelling of numeric input when a source rule examines its characters. */
  responseValueType: external_exports.enum(["number", "text"]).optional(),
  defaultValue: external_exports.union([external_exports.number().finite(), external_exports.string()]).optional()
});
var surveyStructureDateFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("date"),
  dateValueType: surveyDateValueTypeSchema,
  defaultValue: external_exports.string().optional()
});
var surveyStructureBooleanFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("boolean"),
  defaultValue: external_exports.boolean().optional()
});
var surveyStructureDisplayFieldSchema = surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("display")
});
var surveyStructureCustomFieldSchema = external_exports.lazy(() => surveyStructureFieldBaseSchema.extend({
  type: external_exports.literal("custom"),
  childrenFields: external_exports.array(surveyStructureFieldSchema).min(1)
}));
var surveyStructureFieldSchema = external_exports.lazy(() => external_exports.union([
  surveyStructureSingleChoiceFieldSchema,
  surveyStructureMultipleChoiceFieldSchema,
  surveyStructureSingleMatrixFieldSchema,
  surveyStructureMultipleMatrixFieldSchema,
  surveyStructureTextMatrixFieldSchema,
  surveyStructureNumberMatrixFieldSchema,
  surveyStructureDualMatrixFieldSchema,
  surveyStructureMultipleInputFieldSchema,
  surveyStructureTextFieldSchema,
  surveyStructureNumericFieldSchema,
  surveyStructureDateFieldSchema,
  surveyStructureBooleanFieldSchema,
  surveyStructureDisplayFieldSchema,
  surveyStructureCustomFieldSchema
])).superRefine(validateFieldRules);

// dist/schemas/language.js
var surveyLanguageSchema = external_exports.string().min(1).refine((value) => {
  if (/^x(?:-[a-z0-9]{1,8})+$/i.test(value))
    return true;
  try {
    return Intl.getCanonicalLocales(value).length === 1;
  } catch {
    return false;
  }
}, "Use a language tag such as es, es-MX or en.");

// dist/schemas/response-keys.js
function fieldResponseKeys(field, prefix = "") {
  const key = prefix ? `${prefix}_${field.code}` : field.code;
  if (field.type === "display")
    return [];
  if (field.type === "custom")
    return field.childrenFields.flatMap((child) => fieldResponseKeys(child, key));
  if (field.type === "matrix")
    return field.matrix.rows.flatMap((row) => field.matrix.mode === "single" ? [`${key}_${row.code}`] : field.matrix.columns.map((column) => `${key}_${row.code}_${column.code}`));
  if (field.type === "multiple-input")
    return field.subquestions.map((item) => `${key}_${item.code}`);
  if (field.type === "ranking")
    return field.options.map((_, index) => `${key}_${index + 1}`);
  const multiple = field.type === "multiple-choice" || field.type === "multiple-choice-with-comments";
  const keys = multiple ? field.options.flatMap((option) => field.type === "multiple-choice-with-comments" ? [`${key}_${option.code}`, option.commentResponseKey ?? `${key}_${option.code}_comment`] : [`${key}_${option.code}`]) : field.type === "list-with-comment" ? [key, field.commentResponseKey ?? `${key}_comment`] : [key];
  if ("other" in field && field.other) {
    keys.push(field.other.textResponseKey);
    if (field.other.commentResponseKey)
      keys.push(field.other.commentResponseKey);
  }
  return keys;
}

// dist/schemas/survey-invariants.js
var CONDITION_REFERENCE_MISSING_FIELD = "condition-reference-missing-field";
var CONDITION_REFERENCE_MISSING_RESPONSE_ITEM = "condition-reference-missing-response-item";
function validateSurveyInvariants(survey, context) {
  const groups = /* @__PURE__ */ new Set();
  (survey.groups ?? []).forEach((group, index) => {
    if (groups.has(group.id)) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: ["groups", index, "id"],
        message: `Group id ${group.id} is duplicated.`,
        params: { reason: "duplicate-group-id", groupId: group.id }
      });
    }
    groups.add(group.id);
  });
  const fieldsByCode = /* @__PURE__ */ new Map();
  const responseKeys = /* @__PURE__ */ new Set();
  survey.fields.forEach((field, index) => {
    for (const responseKey of fieldResponseKeys(field)) {
      if (responseKeys.has(responseKey))
        context.addIssue({
          code: external_exports.ZodIssueCode.custom,
          path: ["fields", index],
          message: `Response key "${responseKey}" is produced more than once and would overwrite an answer.`,
          params: { reason: "duplicate-response-key", fieldCode: field.code, responseKey }
        });
      responseKeys.add(responseKey);
    }
  });
  const fieldIds = /* @__PURE__ */ new Set();
  const responseItems = /* @__PURE__ */ new Map();
  const itemCodes = (field) => {
    if (!responseItems.has(field))
      responseItems.set(field, fieldResponseItemCodes(field));
    return responseItems.get(field);
  };
  visitFields(survey.fields, (field, path, parent) => {
    if (fieldIds.has(field.id)) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "id"],
        message: `Field id ${field.id} is duplicated.`,
        params: { reason: "duplicate-field-id", fieldId: field.id }
      });
    }
    fieldIds.add(field.id);
    if (fieldsByCode.has(field.code)) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "code"],
        message: `Field code ${field.code} is duplicated.`,
        params: { reason: "duplicate-field-code", fieldCode: field.code }
      });
    }
    fieldsByCode.set(field.code, field);
    if (field.groupId && !groups.has(field.groupId)) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "groupId"],
        message: `groupId ${field.groupId} does not reference a declared group.`,
        params: {
          reason: "field-group-reference-missing",
          fieldCode: field.code,
          groupId: field.groupId
        }
      });
    }
    if (!parent && field.parentId) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "parentId"],
        message: `Top-level field "${field.code}" cannot declare parentId "${field.parentId}".`,
        params: { reason: "top-level-field-has-parent", fieldCode: field.code, parentId: field.parentId }
      });
    }
    if (parent && field.parentId && field.parentId !== parent.id) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "parentId"],
        message: `Child field "${field.code}" declares parentId "${field.parentId}", but its containing field has id "${parent.id}".`,
        params: {
          reason: "child-parent-reference-mismatch",
          fieldCode: field.code,
          parentId: field.parentId,
          expectedParentId: parent.id
        }
      });
    }
    validateResponseItemIdentities(field, path, context, itemCodes);
  });
  visitFields(survey.fields, (field, path) => {
    if (field.type === "multiple-input") {
      for (const rule of ["itemMin", "itemMax", "sumMin", "sumMax", "sumEquals"]) {
        const reference = field.responseValidation?.[`${rule}Reference`];
        if (!reference)
          continue;
        const target = fieldsByCode.get(reference);
        if (target?.type !== "number" || !survey.fields.some((candidate) => candidate.code === reference))
          context.addIssue({
            code: external_exports.ZodIssueCode.custom,
            path: [...path, "responseValidation", `${rule}Reference`],
            message: `The ${rule} reference must identify an existing numeric question.`,
            params: { reason: "numeric-bound-reference-incompatible", fieldCode: reference }
          });
      }
    }
    if ("options" in field)
      field.options.forEach((option, index) => {
        if (option.visibility)
          validateConditionReferences(option.visibility.condition, fieldsByCode, context, [...path, "options", index, "visibility", "condition"], `option "${option.code}" of field "${field.code}"`, itemCodes);
      });
    if (field.type === "matrix")
      field.matrix.rows.forEach((row, index) => {
        if (row.visibility)
          validateConditionReferences(row.visibility.condition, fieldsByCode, context, [...path, "matrix", "rows", index, "visibility", "condition"], `row "${row.code}" of field "${field.code}"`, itemCodes);
      });
    if (field.type === "matrix") {
      field.matrix.columns.forEach((column, index) => {
        if (column.visibility)
          validateConditionReferences(column.visibility.condition, fieldsByCode, context, [...path, "matrix", "columns", index, "visibility", "condition"], `column "${column.code}" of field "${field.code}"`, itemCodes);
      });
      if (field.matrix.mode === "dual-single")
        field.matrix.columns.forEach((column, columnIndex) => {
          column.options.forEach((option, optionIndex) => {
            if (option.visibility)
              validateConditionReferences(option.visibility.condition, fieldsByCode, context, [...path, "matrix", "columns", columnIndex, "options", optionIndex, "visibility", "condition"], `option "${option.code}" of scale "${column.code}" of field "${field.code}"`, itemCodes);
          });
        });
      const cells = /* @__PURE__ */ new Set();
      field.matrix.cells?.forEach((cell, index) => {
        const cellPath = [...path, "matrix", "cells", index];
        const identity = JSON.stringify([cell.rowCode, cell.columnCode]);
        if (cells.has(identity) || !field.matrix.rows.some((row) => row.code === cell.rowCode) || !field.matrix.columns.some((column) => column.code === cell.columnCode))
          context.addIssue({
            code: external_exports.ZodIssueCode.custom,
            path: cellPath,
            message: "Matrix cell rules require unique, declared row and column codes."
          });
        cells.add(identity);
        validateConditionReferences(cell.visibility.condition, fieldsByCode, context, [...cellPath, "visibility", "condition"], `cell "${cell.rowCode}/${cell.columnCode}" of field "${field.code}"`, itemCodes);
      });
    }
    if (field.visibility?.condition) {
      validateConditionReferences(field.visibility.condition, fieldsByCode, context, [...path, "visibility", "condition"], `field "${field.code}"`, itemCodes);
    }
  });
  (survey.groups ?? []).forEach((group, index) => {
    group.navigation?.forEach((rule, ruleIndex) => {
      validateConditionReferences(rule.condition, fieldsByCode, context, ["groups", index, "navigation", ruleIndex, "condition"], `navigation of group "${group.id}"`, itemCodes);
      if ("groupId" in rule.destination && !groups.has(rule.destination.groupId))
        context.addIssue({
          code: external_exports.ZodIssueCode.custom,
          path: ["groups", index, "navigation", ruleIndex, "destination"],
          message: "Navigation destination must reference a declared group."
        });
    });
    if (group.visibility?.condition) {
      validateConditionReferences(group.visibility.condition, fieldsByCode, context, ["groups", index, "visibility", "condition"], `group "${group.title ?? group.id}"`, itemCodes);
    }
  });
}
function validateResponseItemIdentities(field, path, context, itemCodes) {
  if ("options" in field) {
    validateUniqueCodes(field.options, [...path, "options"], "option", field.code, context);
  }
  if (field.type === "multiple-input") {
    validateUniqueCodes(field.subquestions, [...path, "subquestions"], "subquestion", field.code, context);
    const ids = /* @__PURE__ */ new Set();
    field.subquestions.forEach((subquestion, index) => {
      if (!subquestion.id)
        return;
      if (ids.has(subquestion.id)) {
        context.addIssue({
          code: external_exports.ZodIssueCode.custom,
          path: [...path, "subquestions", index, "id"],
          message: `Subquestion id ${subquestion.id} is duplicated inside field ${field.code}.`,
          params: {
            reason: "duplicate-subquestion-id",
            fieldCode: field.code,
            subquestionId: subquestion.id
          }
        });
      }
      ids.add(subquestion.id);
    });
  }
  if (field.type === "matrix") {
    validateUniqueCodes(field.matrix.rows, [...path, "matrix", "rows"], "matrix row", field.code, context);
    validateUniqueCodes(field.matrix.columns, [...path, "matrix", "columns"], "matrix column", field.code, context);
    if (field.matrix.mode === "dual-single")
      field.matrix.columns.forEach((column, index) => {
        validateUniqueCodes(column.options, [...path, "matrix", "columns", index, "options"], "scale option", field.code, context);
      });
  }
  field.source?.responseAliases?.forEach((item, index) => {
    const validAlias = item.responseItemCode === void 0 ? !["display", "multiple-choice", "multiple-choice-with-comments", "matrix", "multiple-input", "ranking", "custom"].includes(field.type) : itemCodes(field).has(item.responseItemCode);
    if (!validAlias)
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "source", "responseAliases", index, "responseItemCode"],
        message: `Source alias refers to an unknown response item in field "${field.code}".`
      });
  });
}
function validateUniqueCodes(items, path, itemName, fieldCode, context) {
  const codes = /* @__PURE__ */ new Set();
  items.forEach((item, index) => {
    if (codes.has(item.code)) {
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, index, "code"],
        message: `${itemName} code ${item.code} is duplicated inside field ${fieldCode}.`,
        params: {
          reason: "duplicate-response-item-code",
          fieldCode,
          responseItemCode: item.code,
          itemType: itemName
        }
      });
    }
    codes.add(item.code);
  });
}
function visitFields(fields, visitor, parentPath = ["fields"], parent) {
  fields.forEach((field, index) => {
    const path = [...parentPath, index];
    visitor(field, path, parent);
    if (field.type === "custom")
      visitFields(field.childrenFields, visitor, [...path, "childrenFields"], field);
  });
}
function validateConditionReferences(condition, fieldsByCode, context, path, owner, itemCodes) {
  if (condition.type === "constant")
    return;
  if (condition.type === "all" || condition.type === "any") {
    condition.conditions.forEach((child, index) => validateConditionReferences(child, fieldsByCode, context, [...path, "conditions", index], owner, itemCodes));
    return;
  }
  if (condition.type === "not") {
    validateConditionReferences(condition.condition, fieldsByCode, context, [...path, "condition"], owner, itemCodes);
    return;
  }
  if (!("responseReference" in condition))
    return;
  const referencedField = fieldsByCode.get(condition.responseReference.fieldCode);
  if (!referencedField) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: [...path, "responseReference", "fieldCode"],
      message: `The visibility condition of ${owner} cannot be evaluated because it references field code "${condition.responseReference.fieldCode}", but no field with that code exists in the normalized survey.`,
      params: {
        reason: CONDITION_REFERENCE_MISSING_FIELD,
        fieldCode: condition.responseReference.fieldCode,
        owner
      }
    });
    return;
  }
  const responseItemCode = condition.responseReference.responseItemCode;
  if ("responseItemCodes" in condition && condition.responseItemCodes) {
    const allowedItems = conditionResponseItemCodes(referencedField);
    const seenItems = /* @__PURE__ */ new Set();
    condition.responseItemCodes.forEach((code, index) => {
      if (!allowedItems.has(code))
        context.addIssue({
          code: external_exports.ZodIssueCode.custom,
          path: [...path, "responseItemCodes", index],
          message: `The aggregate condition of ${owner} references response item "${code}", which field "${referencedField.code}" does not produce.`,
          params: { reason: CONDITION_REFERENCE_MISSING_RESPONSE_ITEM, fieldCode: referencedField.code, responseItemCode: code, owner }
        });
      if (seenItems.has(code))
        context.addIssue({
          code: external_exports.ZodIssueCode.custom,
          path: [...path, "responseItemCodes", index],
          message: `Response item "${code}" occurs more than once in the aggregate condition of ${owner}. Each response may contribute only once.`,
          params: { reason: "duplicate-aggregate-response-item-code", fieldCode: referencedField.code, responseItemCode: code, owner }
        });
      seenItems.add(code);
    });
  }
  if (responseItemCode && !conditionResponseItemCodes(referencedField).has(responseItemCode)) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: [...path, "responseReference", "responseItemCode"],
      message: `The visibility condition of ${owner} references response item code "${responseItemCode}", but field "${referencedField.code}" does not produce that scalar response item in this variant.`,
      params: {
        reason: CONDITION_REFERENCE_MISSING_RESPONSE_ITEM,
        fieldCode: referencedField.code,
        responseItemCode,
        owner
      }
    });
  }
  if (condition.type === "comparison") {
    const collection = ["custom", "display", "multiple-input", "multiple-choice", "multiple-choice-with-comments", "ranking", "matrix"].includes(referencedField.type);
    if (collection && !responseItemCode)
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "responseReference"],
        message: "A comparison requires one scalar response, not an entire collection or display field.",
        params: { reason: "comparison-requires-scalar-response", fieldCode: referencedField.code, owner }
      });
    if (!comparisonValueMatches(referencedField, responseItemCode, condition.value))
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "value"],
        message: "The comparison value does not match the referenced response type or its declared options.",
        params: { reason: "comparison-value-type-mismatch", fieldCode: referencedField.code, responseItemCode, owner }
      });
  }
  if (condition.type === "pattern-match") {
    const scalarText = referencedField.type === "short-text" || referencedField.type === "long-text" || referencedField.type === "number" && referencedField.responseValueType === "text" || referencedField.type === "multiple-input" && !!responseItemCode || referencedField.type === "matrix" && referencedField.matrix.mode === "text" && !!responseItemCode;
    if (!scalarText)
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "responseReference"],
        message: "A pattern condition requires one text response.",
        params: { reason: "pattern-requires-text-response", fieldCode: referencedField.code, owner }
      });
  }
  if (condition.type === "selection-count" && !(referencedField.type === "multiple-choice" || referencedField.type === "multiple-choice-with-comments" || referencedField.type === "ranking" || referencedField.type === "matrix" && referencedField.matrix.mode === "multiple")) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: [...path, "responseReference", "fieldCode"],
      message: `The selection-count condition of ${owner} requires a field that can contain multiple selected responses; field "${referencedField.code}" has type "${referencedField.type}".`,
      params: {
        reason: "selection-count-incompatible-field-type",
        fieldCode: referencedField.code,
        semanticFieldType: referencedField.type,
        owner
      }
    });
  }
  if (condition.type === "answered-count" && !(referencedField.type === "multiple-input" || referencedField.type === "multiple-choice" || referencedField.type === "matrix" && referencedField.matrix.mode !== "multiple")) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: [...path, "responseReference", "fieldCode"],
      message: `Answered-count requires multiple inputs or matrix response cells in field "${referencedField.code}".`,
      params: { reason: "answered-count-incompatible-field-type", fieldCode: referencedField.code, owner }
    });
  }
  if (["selection-count", "answered-count"].includes(condition.type) && responseItemCode) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: [...path, "responseReference", "responseItemCode"],
      message: "A count refers to the entire question, not an individual response item.",
      params: { reason: "count-requires-whole-field", fieldCode: referencedField.code, owner }
    });
  }
  if (condition.type === "numeric-aggregate") {
    if (referencedField.type !== "matrix" || referencedField.matrix.mode !== "number")
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "responseReference", "fieldCode"],
        message: `A numeric aggregate requires numeric matrix cells; field "${referencedField.code}" does not declare numeric cells.`,
        params: { reason: "numeric-aggregate-incompatible-field-type", fieldCode: referencedField.code, owner }
      });
    if (responseItemCode)
      context.addIssue({
        code: external_exports.ZodIssueCode.custom,
        path: [...path, "responseReference", "responseItemCode"],
        message: "An aggregate identifies its question with responseReference and any subset with responseItemCodes.",
        params: { reason: "aggregate-requires-whole-field", fieldCode: referencedField.code, owner }
      });
  }
  if (condition.type === "comparison" && [
    "greater-than",
    "greater-than-or-equal",
    "less-than",
    "less-than-or-equal"
  ].includes(condition.operator) && ![
    "number",
    "range",
    "date"
  ].includes(referencedField.type) && !(referencedField.type === "matrix" && referencedField.matrix.mode === "number" && referencedField.matrix.rows.some((row) => referencedField.matrix.columns.some((column) => `${row.code}_${column.code}` === responseItemCode)))) {
    context.addIssue({
      code: external_exports.ZodIssueCode.custom,
      path: [...path, "operator"],
      message: `The visibility condition of ${owner} uses operator "${condition.operator}" with field "${referencedField.code}" of type "${referencedField.type}", which is not compatible with ordered comparison.`,
      params: {
        reason: "ordered-comparison-incompatible-field-type",
        fieldCode: referencedField.code,
        semanticFieldType: referencedField.type,
        operator: condition.operator,
        owner
      }
    });
  }
}
function fieldResponseItemCodes(field) {
  if (field.type === "ranking")
    return new Set(field.options.map((_, index) => String(index + 1)));
  if ("options" in field)
    return new Set(field.options.map((option) => option.code));
  if (field.type === "multiple-input")
    return new Set(field.subquestions.map((item) => item.code));
  if (field.type === "matrix") {
    const values = /* @__PURE__ */ new Set();
    field.matrix.rows.forEach((row) => {
      values.add(row.code);
      field.matrix.columns.forEach((column) => values.add(`${row.code}_${column.code}`));
    });
    return values;
  }
  return /* @__PURE__ */ new Set();
}
function conditionResponseItemCodes(field) {
  if (field.type === "multiple-choice" || field.type === "multiple-choice-with-comments") {
    return /* @__PURE__ */ new Set([...field.options.map((option) => option.code), ...field.other ? [field.other.code] : []]);
  }
  if (field.type === "matrix")
    return new Set(field.matrix.rows.flatMap((row) => field.matrix.mode === "single" ? [row.code] : field.matrix.columns.map((column) => `${row.code}_${column.code}`)));
  if (field.type === "ranking" || field.type === "multiple-input")
    return fieldResponseItemCodes(field);
  return /* @__PURE__ */ new Set();
}
function comparisonValueMatches(field, item, value) {
  if (value === null)
    return true;
  if (field.type === "number" || field.type === "range" || field.type === "matrix" && field.matrix.mode === "number")
    return typeof value === "number";
  if (field.type === "multiple-input")
    return true;
  if (field.type === "boolean" || field.type === "multiple-choice" || field.type === "multiple-choice-with-comments" || field.type === "matrix" && field.matrix.mode === "multiple") {
    return typeof value === "boolean" || value === field.responseEncoding?.selectedValue || value === field.responseEncoding?.unselectedValue;
  }
  if (field.type === "matrix" && field.matrix.mode === "single")
    return field.matrix.columns.some((column) => column.code === value);
  if (field.type === "matrix" && field.matrix.mode === "dual-single") {
    const scale = field.matrix.columns.find((column) => field.matrix.rows.some((row) => `${row.code}_${column.code}` === item));
    return scale?.options.some((option) => option.code === value) ?? false;
  }
  if ("options" in field)
    return field.options.some((option) => option.code === value) || value === field.other?.code;
  return typeof value === "string";
}

// dist/schemas/survey.js
var SURVEY_STRUCTURE_VERSION = "2.1.0";
var surveyStructureSchema = external_exports.object({
  surveyStructureVersion: external_exports.literal(SURVEY_STRUCTURE_VERSION),
  id: external_exports.string().min(1),
  title: external_exports.string().optional(),
  description: external_exports.string().optional(),
  language: surveyLanguageSchema.optional(),
  availableLanguages: external_exports.array(surveyLanguageSchema).optional(),
  groups: external_exports.array(surveyStructureGroupSchema).optional(),
  fields: external_exports.array(surveyStructureFieldSchema),
  settings: surveyStructureSettingsSchema.optional(),
  source: surveyStructureSourceSchema.optional()
}).strict().superRefine(validateSurveyInvariants);

// dist/schemas/diagnostics.js
var surveyStructureIssueCodeSchema = external_exports.enum([
  "INVALID_SOURCE",
  "UNSUPPORTED_SOURCE_VERSION",
  "UNSUPPORTED_TYPE",
  "MISSING_QUESTION_CODE",
  "DUPLICATE_QUESTION_CODE",
  "MISSING_PARENT",
  "EMPTY_OPTIONS",
  "INVALID_EXPRESSION",
  "INVALID_VALIDATION",
  "UNCONVERTED_SOURCE_PROPERTY",
  "MISSING_CONDITION_REFERENCE",
  "UNSUPPORTED_SOURCE_EXPRESSION",
  "SOURCE_SCRIPT_NOT_EXECUTED",
  "UNSUPPORTED_TIMER",
  "UNSUPPORTED_TIMER_SETTING",
  "UNSUPPORTED_LOCATION_SETTING"
]);
var surveyStructureIssueBaseSchema = external_exports.object({
  level: external_exports.enum(["warning", "error"]),
  message: external_exports.string().min(1),
  fieldId: external_exports.string().optional(),
  questionCode: external_exports.string().optional()
});
var surveyStructureIssueSchema = external_exports.discriminatedUnion("code", [
  surveyStructureIssueBaseSchema.extend({
    code: external_exports.enum(["UNCONVERTED_SOURCE_PROPERTY", "UNSUPPORTED_TIMER_SETTING", "UNSUPPORTED_LOCATION_SETTING"]),
    details: external_exports.object({ propertyName: external_exports.string(), sourceValue: external_exports.string() }).strict()
  }).strict(),
  surveyStructureIssueBaseSchema.extend({
    code: external_exports.literal("UNSUPPORTED_TYPE"),
    details: external_exports.object({ sourceType: external_exports.string() }).strict()
  }).strict(),
  surveyStructureIssueBaseSchema.extend({
    code: external_exports.enum(["INVALID_EXPRESSION", "MISSING_CONDITION_REFERENCE", "UNSUPPORTED_SOURCE_EXPRESSION", "SOURCE_SCRIPT_NOT_EXECUTED"]),
    details: external_exports.object({
      sourceExpression: external_exports.string(),
      rule: external_exports.string().optional(),
      scope: external_exports.enum(["survey", "group", "field"]).optional(),
      rowCode: external_exports.string().optional(),
      childQuestionId: external_exports.string().optional()
    }).strict()
  }).strict(),
  surveyStructureIssueBaseSchema.extend({
    code: external_exports.literal("UNSUPPORTED_SOURCE_VERSION"),
    details: external_exports.object({ sourceVersion: external_exports.string() }).strict()
  }).strict(),
  surveyStructureIssueBaseSchema.extend({
    code: external_exports.enum(["INVALID_VALIDATION", "UNSUPPORTED_TIMER"]),
    details: external_exports.object({
      // Source attribute name, not a SurveyValidationReason; adapters may add native rules.
      rule: external_exports.string(),
      sourceValue: external_exports.union([external_exports.string(), external_exports.number().finite(), external_exports.boolean(), external_exports.null()]).optional()
    }).strict()
  }).strict(),
  surveyStructureIssueBaseSchema.extend({
    code: external_exports.literal("EMPTY_OPTIONS"),
    details: external_exports.object({
      omitted: external_exports.boolean(),
      rows: external_exports.number().int().nonnegative().optional(),
      columns: external_exports.number().int().nonnegative().optional()
    }).strict().optional()
  }).strict(),
  surveyStructureIssueBaseSchema.extend({
    code: external_exports.enum([
      "INVALID_SOURCE",
      "MISSING_QUESTION_CODE",
      "DUPLICATE_QUESTION_CODE",
      "MISSING_PARENT"
    ])
  }).strict()
]);

// dist/schemas/load-result.js
var surveyResponseStateSchema = external_exports.object({
  active: external_exports.boolean(),
  canSaveResponses: external_exports.boolean(),
  submitMode: external_exports.enum(["submit", "submit_preview"]),
  language: external_exports.string().optional(),
  endText: external_exports.string().optional(),
  warningCodes: external_exports.array(external_exports.string()),
  didNotSaveCode: external_exports.string().nullable()
}).strict();
var surveyLoadResultSchema = external_exports.object({
  survey: surveyStructureSchema,
  issues: external_exports.array(surveyStructureIssueSchema),
  responseState: surveyResponseStateSchema.optional(),
  // Measured by the source adapter before filtering; never inferred from output fields.
  sourceMetrics: external_exports.object({
    topLevelQuestions: external_exports.number().int().nonnegative(),
    childQuestions: external_exports.number().int().nonnegative(),
    integratedChildren: external_exports.number().int().nonnegative(),
    detectedTypes: external_exports.array(external_exports.string()),
    conditionsDetected: external_exports.number().int().nonnegative(),
    validationQuestions: external_exports.number().int().nonnegative()
  }).strict().refine((value) => value.integratedChildren <= value.childQuestions, {
    message: "Integrated children cannot exceed source children.",
    path: ["integratedChildren"]
  }).optional()
}).strict();

// dist/validation-diagnostics.js
var messages = {
  "duplicate-group-id": ["The group id is duplicated.", "El identificador del grupo est\xE1 duplicado."],
  "duplicate-response-key": ["The response key is produced more than once and would overwrite an answer.", "La clave de respuesta se genera m\xE1s de una vez y sobrescribir\xEDa una respuesta."],
  "duplicate-field-id": ["The field id is duplicated.", "El identificador de la pregunta est\xE1 duplicado."],
  "duplicate-field-code": ["The field code is duplicated.", "El c\xF3digo de la pregunta est\xE1 duplicado."],
  "field-group-reference-missing": ["The field references a group that does not exist.", "La pregunta hace referencia a un grupo que no existe."],
  "top-level-field-has-parent": ["A top-level field cannot declare a parent.", "Una pregunta de primer nivel no puede declarar una pregunta padre."],
  "child-parent-reference-mismatch": ["The parent id does not match the containing field.", "El identificador de la pregunta padre no coincide con el contenedor."],
  "duplicate-subquestion-id": ["The subquestion id is duplicated.", "El identificador de la subpregunta est\xE1 duplicado."],
  "duplicate-response-item-code": ["The response item code is duplicated within the field.", "El c\xF3digo del elemento de respuesta est\xE1 duplicado dentro de la pregunta."],
  "condition-reference-missing-field": ["The condition references a field that does not exist.", "La condici\xF3n hace referencia a una pregunta que no existe."],
  "condition-reference-missing-response-item": ["The condition references a response item that the field does not produce.", "La condici\xF3n hace referencia a un elemento de respuesta que la pregunta no genera."],
  "duplicate-aggregate-response-item-code": ["An aggregate cannot include the same response item more than once.", "Una agregaci\xF3n no puede incluir el mismo elemento de respuesta m\xE1s de una vez."],
  "comparison-requires-scalar-response": ["A comparison requires one scalar response, not a collection or display field.", "Una comparaci\xF3n requiere una respuesta escalar, no una colecci\xF3n ni un elemento informativo."],
  "pattern-requires-text-response": ["A pattern condition requires one text response.", "La condici\xF3n con patr\xF3n requiere una respuesta de texto."],
  "numeric-bound-reference-incompatible": ["A numeric limit must reference an existing numeric question.", "El l\xEDmite num\xE9rico debe consultar una pregunta num\xE9rica existente."],
  "comparison-value-type-mismatch": ["The comparison value does not match the response type or its declared options.", "El valor de comparaci\xF3n no coincide con el tipo de respuesta ni con sus opciones declaradas."],
  "selection-count-incompatible-field-type": ["Selection-count requires a field with multiple selected responses.", "El conteo de selecciones requiere una pregunta que permita varias respuestas seleccionadas."],
  "answered-count-incompatible-field-type": ["Answered-count requires multiple inputs or matrix response cells.", "El conteo de respuestas requiere varias entradas o celdas de respuesta de una matriz."],
  "count-requires-whole-field": ["A count refers to the entire question, not an individual response item.", "Un conteo hace referencia a la pregunta completa, no a un elemento de respuesta individual."],
  "numeric-aggregate-incompatible-field-type": ["A numeric aggregation requires numeric matrix cells.", "Una agregaci\xF3n num\xE9rica requiere celdas num\xE9ricas de una matriz."],
  "aggregate-requires-whole-field": ["An aggregate identifies its question with responseReference and its subset with responseItemCodes.", "Una agregaci\xF3n identifica su pregunta con responseReference y su subconjunto con responseItemCodes."],
  "ordered-comparison-incompatible-field-type": ["The response type is not compatible with an ordered comparison.", "El tipo de respuesta no es compatible con una comparaci\xF3n de orden."],
  "widget-not-compatible-with-field-type": ["The widget is not compatible with the field type.", "El componente visual no es compatible con el tipo de pregunta."],
  "other-option-code-collision": ["The other-response code duplicates an option code.", "El c\xF3digo de la respuesta \xABOtro\xBB coincide con el c\xF3digo de una opci\xF3n."],
  "other-comment-key-incompatible-field-type": ["An other-response comment key is not supported by this field type.", "Este tipo de pregunta no admite una clave de comentario para la respuesta \xABOtro\xBB."],
  "other-response-incompatible-field-type": ["This field type does not support an other response.", "Este tipo de pregunta no admite la respuesta \xABOtro\xBB."],
  "date-default-value-format-mismatch": ["The default date does not match its declared date format.", "La fecha predeterminada no coincide con el formato de fecha declarado."],
  "response-encoding-incompatible-field-type": ["This field type does not support selected/unselected response encoding.", "Este tipo de pregunta no admite una codificaci\xF3n de respuesta seleccionada/no seleccionada."],
  "response-encoding-value-type-mismatch": ["The encoded response values do not match the field type.", "Los valores de respuesta codificados no coinciden con el tipo de pregunta."],
  "response-encoding-label-pair-incomplete": ["Selected and unselected labels must be declared together.", "Las etiquetas de selecci\xF3n y no selecci\xF3n deben declararse juntas."],
  "default-value-validation-mismatch": ["The default value does not satisfy the declared validation rules.", "El valor predeterminado no cumple las reglas de validaci\xF3n declaradas."],
  "duplicate-default-option-code": ["The default value contains a duplicated option code.", "El valor predeterminado contiene un c\xF3digo de opci\xF3n duplicado."],
  "ranking-default-not-a-complete-order": ["The default ranking must contain every option exactly once.", "El orden predeterminado debe contener cada opci\xF3n exactamente una vez."],
  "default-value-reference-missing": ["The default value references an option or response item that does not exist.", "El valor predeterminado hace referencia a una opci\xF3n o elemento de respuesta que no existe."],
  "validation-rule-not-applicable": ["The validation rule is not applicable to this field type.", "La regla de validaci\xF3n no se aplica a este tipo de pregunta."],
  "invalid-validation-pattern": ["The validation pattern must be a valid ECMAScript regular expression without flags.", "El patr\xF3n de validaci\xF3n debe ser una expresi\xF3n regular v\xE1lida de ECMAScript sin indicadores."]
};
var structuralMessages = {
  invalid_type: ["The value has an invalid type.", "El valor tiene un tipo no v\xE1lido."],
  invalid_literal: ["The value does not match the required literal.", "El valor no coincide con el literal requerido."],
  invalid_union: ["The value does not match any supported variant.", "El valor no coincide con ninguna variante admitida."],
  invalid_union_discriminator: ["The variant discriminator is invalid.", "El discriminador de la variante no es v\xE1lido."],
  invalid_enum_value: ["The value is not one of the allowed options.", "El valor no es una de las opciones permitidas."],
  unrecognized_keys: ["The object contains unknown properties.", "El objeto contiene propiedades desconocidas."],
  invalid_arguments: ["The function arguments are invalid.", "Los argumentos de la funci\xF3n no son v\xE1lidos."],
  invalid_return_type: ["The function return type is invalid.", "El tipo de retorno de la funci\xF3n no es v\xE1lido."],
  invalid_date: ["The date is invalid.", "La fecha no es v\xE1lida."],
  invalid_string: ["The text does not match the required format.", "El texto no cumple el formato requerido."],
  too_small: ["The value is below the allowed minimum.", "El valor es inferior al m\xEDnimo permitido."],
  too_big: ["The value exceeds the allowed maximum.", "El valor supera el m\xE1ximo permitido."],
  invalid_intersection_types: ["The validated variants cannot be merged.", "No se pueden combinar las variantes validadas."],
  not_multiple_of: ["The value is not a multiple of the required number.", "El valor no es m\xFAltiplo del n\xFAmero requerido."],
  not_finite: ["The number must be finite.", "El n\xFAmero debe ser finito."]
};
function resolveSurveyDiagnosticLocale(locale) {
  return typeof locale === "string" && /^es(?:[-_]|$)/i.test(locale.trim()) ? "es" : "en";
}
function localizeSurveyValidationIssue(issue, locale) {
  const reason = issue.params?.reason;
  const spanish = resolveSurveyDiagnosticLocale(locale) === "es";
  if (typeof reason !== "string" || !Object.hasOwn(messages, reason)) {
    if (!spanish)
      return issue.message;
    if (!Object.hasOwn(structuralMessages, issue.code))
      return issue.message;
    if (issue.code === "invalid_type" && issue.received === "undefined")
      return "El valor es obligatorio.";
    const message2 = structuralMessages[issue.code][spanish ? 1 : 0];
    const detail = issue.keys?.join(", ") ?? issue.expected ?? issue.minimum ?? issue.maximum;
    return detail === void 0 ? message2 : `${message2} (${String(detail)})`;
  }
  const params = issue.params ?? {};
  if (reason === "condition-reference-missing-field") {
    const owner = typeof params.owner === "string" ? params.owner : "";
    const fieldCode = typeof params.fieldCode === "string" ? params.fieldCode : "";
    if (owner && fieldCode)
      return spanish ? `La condici\xF3n de visibilidad de ${owner.replace(/^field /, "la pregunta ").replace(/^group /, "el grupo ")} hace referencia al c\xF3digo de pregunta "${fieldCode}", pero no existe ninguna pregunta con ese c\xF3digo en la encuesta normalizada.` : `The visibility condition of ${owner} cannot be evaluated because it references field code "${fieldCode}", but no field with that code exists in the normalized survey.`;
  }
  const message = messages[reason][spanish ? 1 : 0];
  return typeof params.fieldCode === "string" ? `${message} (${params.fieldCode})` : message;
}

// scripts/validate-survey.mjs
var schemas = { SurveyStructure: surveyStructureSchema, SurveyLoadResult: surveyLoadResultSchema };
function describe(issue, locale) {
  if (issue.code !== "invalid_union") return localizeSurveyValidationIssue(issue, locale);
  const branch = [...issue.unionErrors].sort((a, b) => a.issues.length - b.issues.length)[0];
  return branch.issues.map((child) => describe(child, locale)).join("; ");
}
try {
  const { contract, value, locale = "en" } = JSON.parse((0, import_node_fs.readFileSync)(0, "utf8"));
  if (!Object.hasOwn(schemas, contract)) throw new Error("Unknown contract");
  const result = schemas[contract].safeParse(value);
  process.stdout.write(JSON.stringify(result.success ? { success: true } : { success: false, issues: result.error.issues.map((issue) => ({ path: issue.path, code: issue.code, message: describe(issue, locale), params: issue.params })) }));
} catch {
  process.stderr.write("Survey contract validator could not process its input.\n");
  process.exitCode = 2;
}
