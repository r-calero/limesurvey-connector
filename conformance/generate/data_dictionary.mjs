// Record dictionaries, CSV exports and response translations from the reference packages.
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';

const { values: args } = parseArgs({
  options: {
    dictionary: { type: 'string' },
    service: { type: 'string' },
    fixtures: { type: 'string' },
    goldens: { type: 'string' },
    out: { type: 'string' },
  },
});
const fixtures = resolve(args.fixtures);
const goldens = resolve(args.goldens);
const out = resolve(args.out);
const sdd = await import(pathToFileURL(join(resolve(args.dictionary), 'dist/index.js')).href);
const { csvToCanonicalResponses } = await import(pathToFileURL(join(resolve(args.service), 'dist/csv-dataset.js')).href);

const readJson = (path) => JSON.parse(readFileSync(path, 'utf8'));

function writeFile(directory, filename, content) {
  mkdirSync(directory, { recursive: true });
  writeFileSync(join(directory, filename), content);
}
const writeJson = (directory, filename, value) => writeFile(directory, filename, `${JSON.stringify(value, null, 2)}\n`);

function attempt(action) {
  try {
    return { ok: true, result: action() };
  } catch (error) {
    return {
      ok: false,
      error: {
        name: error.name,
        message: error.message,
        ...(error.issues ? { issues: JSON.parse(JSON.stringify(error.issues)) } : {}),
        ...(error.statusCode ? { statusCode: error.statusCode } : {}),
      },
    };
  }
}

function surveyInput(fixture) {
  if (fixture.structure) return { survey: fixture.structure, sourceIssues: [] };
  if (fixture.structureFixture) return { survey: readJson(join(fixtures, fixture.structureFixture)).value, sourceIssues: [] };
  const golden = readJson(join(goldens, fixture.loadResultGolden));
  if (!golden.ok) throw new Error(`${fixture.loadResultGolden} does not contain a load result.`);
  return { survey: golden.result.survey, sourceIssues: golden.result.issues };
}

const SYSTEM_CHANGE = 'system-columns';
// Fixed columns only; timing and pattern columns are covered by the connector's own tests.
const SYSTEM_COLUMNS = readJson(join(fixtures, '..', '..', 'src', 'limesurvey_connector', 'limesurvey', 'system_columns.json'))
  .columns.filter((column) => !column.pattern && !column.timing);
const normalizeHeader = (value) => `${value}`.normalize('NFKC').replace(/\u00a0/g, ' ').replace(/\s+/g, ' ').trim();

// Connector behavior for the system-columns change (conformance/intentional-changes.json).
// The reference packages still do the mapping and translation; this only prepares their inputs.
function systemColumnsIn(keys) {
  const present = new Set(keys.map(normalizeHeader));
  return SYSTEM_COLUMNS.filter((column) => present.has(column.code)
    || column.headers.some((header) => present.has(normalizeHeader(header))));
}

function withSystemFields(dictionary, columns) {
  const taken = new Set(dictionary.fields.map((field) => field.responseKey));
  const language = /^es(?:[-_]|$)/i.test(dictionary.language ?? '') ? 'es' : 'en';
  const entries = columns.filter((column) => !taken.has(column.code)).map((column) => ({
    questionCode: column.code,
    questionLabel: column.labels[language],
    responseKey: column.code,
    dataType: column.dataType,
    cardinality: 'single',
    aliases: column.headers,
  }));
  return { ...dictionary, fields: [...entries, ...dictionary.fields] };
}

const isAnswerColumn = (column) => column.role !== 'response-id';

function responseIdHeaders(dictionary) {
  const taken = new Set(dictionary.fields.map((field) => field.responseKey));
  const column = SYSTEM_COLUMNS.find((item) => item.role === 'response-id');
  return [...column.headers, column.code].filter((header) => !taken.has(header));
}

// Mirrors POST /v1/responses/translate in limesurvey-dictionary-api.
function translateJson(dictionary, request) {
  const ignoredKeys = [];
  let responseIds = request.responseIds;
  if (request.responseIdKey) {
    responseIds = request.responses.map((response) => {
      const value = response[request.responseIdKey];
      return value === null || ['string', 'number', 'boolean'].includes(typeof value) ? value : undefined;
    });
    ignoredKeys.push(request.responseIdKey);
  }
  ignoredKeys.push(...(request.ignoredKeys ?? []));
  let target = dictionary;
  if (request.change === SYSTEM_CHANGE) {
    const keys = [...new Set(request.responses.flatMap((response) => Object.keys(response)))]
      .filter((key) => !ignoredKeys.includes(key));
    target = withSystemFields(dictionary, systemColumnsIn(keys).filter(isAnswerColumn));
  }
  return sdd.translateDataset(target, request.responses, {
    responseIds,
    ignoredKeys,
    unmappedValues: request.unmappedValues,
  });
}

function translateCsv(dictionary, request, aliasConfiguration) {
  const csv = readFileSync(join(fixtures, request.file), 'utf8');
  const ignoredHeaders = [...(aliasConfiguration?.ignoredHeaders ?? []), ...(request.options?.ignoredHeaders ?? [])];
  const options = {
    ...request.options,
    ignoredHeaders,
    defaultIgnoredHeaders: [],
    responseIdHeaders: responseIdHeaders(dictionary),
  };
  const { headers } = csvToCanonicalResponses(csv, dictionary, options);
  const present = headers.filter((header) => !ignoredHeaders.includes(header));
  const target = withSystemFields(dictionary, systemColumnsIn(present).filter(isAnswerColumn));
  const converted = csvToCanonicalResponses(csv, target, options);
  const translated = sdd.translateDataset(target, converted.responses, {
    unmappedValues: converted.unmappedValues,
    responseIds: converted.responseIds,
    ignoredKeys: [],
  });
  translated.issues.unshift(...converted.issues);
  return { canonical: converted, translated };
}

function emitCase(name, fixture) {
  const directory = join(out, name);
  const input = attempt(() => surveyInput(fixture));
  if (!input.ok) throw new Error(`${name}: ${input.error.message}`);
  const aliasConfiguration = fixture.aliasConfiguration;
  const built = attempt(() => sdd.buildSurveyDictionary(input.result.survey, {
    aliases: aliasConfiguration?.aliases,
    sourceIssues: input.result.sourceIssues,
    ...(fixture.strict ? { strict: true } : {}),
  }));
  writeJson(directory, 'dictionary.json', { fixture: fixture.origin, ...built });
  if (!built.ok) return;
  const dictionary = built.result;
  writeFile(directory, 'dictionary.csv', sdd.dictionaryToCsv(dictionary));

  if (fixture.includeSystemFields) {
    const extended = withSystemFields(dictionary, SYSTEM_COLUMNS);
    writeJson(directory, 'dictionary-system.json', { change: SYSTEM_CHANGE, ok: true, result: extended });
    writeFile(directory, 'dictionary-system.csv', sdd.dictionaryToCsv(extended));
  }
  for (const questionCode of fixture.questionCodes ?? []) {
    writeJson(directory, `question-${questionCode}.json`, sdd.getQuestionDictionary(dictionary, questionCode));
  }
  for (const request of fixture.translations ?? []) {
    const translated = attempt(() => translateJson(dictionary, request));
    writeJson(directory, `translate-${request.name}.json`, request.change ? { change: request.change, ...translated } : translated);
    if (translated.ok) writeFile(directory, `translate-${request.name}.csv`, sdd.translatedDatasetToCsv(translated.result));
  }
  for (const request of fixture.csv ?? []) {
    const result = attempt(() => translateCsv(dictionary, request, aliasConfiguration));
    writeJson(directory, `csv-${request.name}.json`, { change: SYSTEM_CHANGE, ...result });
    if (result.ok) writeFile(directory, `csv-${request.name}.csv`, sdd.translatedDatasetToCsv(result.result.translated));
  }
  for (const request of fixture.tabular ?? []) {
    writeJson(directory, `tabular-${request.name}.json`, attempt(() => sdd.mapTabularDataset(
      dictionary, request.headers, request.rows, request.ignoredHeaders, request.missingValues, request.responseIdHeaders,
    )));
  }
}

const dictionaryFixtures = join(fixtures, 'dictionary');
for (const filename of readdirSync(dictionaryFixtures).filter((file) => file.endsWith('.json')).sort()) {
  emitCase(filename.replace(/\.json$/, ''), { ...readJson(join(dictionaryFixtures, filename)), origin: `fixtures/dictionary/${filename}` });
}

// Every successfully imported .lss also gets a plain dictionary.
const lssGoldens = join(goldens, 'limesurvey', 'lss');
if (existsSync(lssGoldens)) {
  for (const filename of readdirSync(lssGoldens).filter((file) => file.endsWith('.json')).sort()) {
    if (!readJson(join(lssGoldens, filename)).ok) continue;
    const loadResultGolden = `limesurvey/lss/${filename}`;
    emitCase(`lss-${filename.replace(/\.json$/, '')}`, { loadResultGolden, origin: loadResultGolden });
  }
}

// Parser and schema behavior on edge-case inputs.
const { createRequire } = await import('node:module');
const requireFromService = createRequire(join(resolve(args.service), 'package.json'));
const Papa = requireFromService('papaparse');
const edge = readJson(join(fixtures, 'data-dictionary-cases.json'));
const casesDirectory = join(goldens, 'data-dictionary-cases');
writeJson(casesDirectory, 'csv-parse.json', edge.csv.map((item) => {
  const parsed = Papa.parse(item.text, { ...(item.delimiter ? { delimiter: item.delimiter } : {}), skipEmptyLines: true });
  return { name: item.name, data: parsed.data, errors: parsed.errors, delimiter: parsed.meta.delimiter, linebreak: parsed.meta.linebreak };
}));
const schemas = {
  SurveyDictionary: sdd.surveyDictionarySchema,
  SurveyResponseDataset: sdd.surveyResponseDatasetSchema,
  SurveyResponseRecord: sdd.surveyResponseRecordSchema,
};
const serializeIssue = (issue) => {
  const { unionErrors, ...rest } = issue;
  const serialized = JSON.parse(JSON.stringify(rest));
  if (unionErrors) serialized.unionErrors = unionErrors.map((error) => error.issues.map(serializeIssue));
  return serialized;
};
writeJson(casesDirectory, 'schema-cases.json', edge.schemas.map((item) => {
  const parsed = schemas[item.contract].safeParse(item.value);
  return {
    ...item,
    success: parsed.success,
    ...(parsed.success ? { data: parsed.data } : { issues: parsed.error.issues.map(serializeIssue) }),
  };
}));
