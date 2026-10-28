// Record survey-structure validation results, localized diagnostics and readiness checks.
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';

const { values: args } = parseArgs({
  options: { package: { type: 'string' }, fixtures: { type: 'string' }, out: { type: 'string' } },
});
const packageDirectory = resolve(args.package);
const contract = await import(pathToFileURL(join(packageDirectory, 'dist/index.js')).href);
const { default: referenceCases } = await import(pathToFileURL(join(packageDirectory, 'test/validation-cases.mjs')).href);

const schemas = {
  SurveyStructure: contract.surveyStructureSchema,
  SurveyLoadResult: contract.surveyLoadResultSchema,
};

function serializeIssue(issue) {
  const { unionErrors, ...rest } = issue;
  const serialized = JSON.parse(JSON.stringify(rest));
  if (unionErrors) serialized.unionErrors = unionErrors.map((error) => error.issues.map(serializeIssue));
  return serialized;
}

function evaluate(name, contractName, value, expectedValid, origin) {
  const parsed = schemas[contractName].safeParse(value);
  if (expectedValid !== undefined && parsed.success !== expectedValid) {
    throw new Error(`Case "${name}" was expected to be ${expectedValid ? 'valid' : 'invalid'}.`);
  }
  const issues = parsed.success ? [] : parsed.error.issues;
  return {
    name,
    origin,
    contract: contractName,
    value,
    success: parsed.success,
    issues: issues.map(serializeIssue),
    messages: {
      en: issues.map((issue) => contract.localizeSurveyValidationIssue(issue, 'en')),
      es: issues.map((issue) => contract.localizeSurveyValidationIssue(issue, 'es')),
    },
    ...(parsed.success && contractName === 'SurveyStructure'
      ? { executionIssues: contract.getSurveyExecutionIssues(parsed.data) }
      : {}),
  };
}

const cases = referenceCases.map((item) => evaluate(item.name, item.contract, item.value, item.valid, 'survey-structure/test/validation-cases.mjs'));

const structureDirectory = join(resolve(args.fixtures), 'structures');
for (const filename of readdirSync(structureDirectory).filter((file) => file.endsWith('.json')).sort()) {
  const fixture = JSON.parse(readFileSync(join(structureDirectory, filename), 'utf8'));
  cases.push(evaluate(filename, fixture.contract ?? 'SurveyStructure', fixture.value, fixture.valid, `fixtures/structures/${filename}`));
}

const edge = JSON.parse(readFileSync(join(resolve(args.fixtures), 'contract-cases.json'), 'utf8'));
for (const item of edge.cases) {
  cases.push(evaluate(item.name, item.contract, item.value, undefined, 'fixtures/contract-cases.json'));
}

const emptySurvey = { surveyStructureVersion: contract.SURVEY_STRUCTURE_VERSION, id: 'language', fields: [] };
const languageTags = edge.languageTags.map((tag) => ({
  tag,
  valid: contract.surveyStructureSchema.safeParse({ ...emptySurvey, language: tag }).success,
}));

const compactIssue = (issue) => ({ path: issue.path, code: issue.code, ...(issue.params?.reason ? { reason: issue.params.reason } : {}) });
const patternCases = edge.patterns.flatMap((pattern) => edge.patternFlagSets.flatMap((flags) => edge.patternValues.map((value) => {
  const responseValidation = { responseFormatPattern: pattern, ...(flags ? { patternFlags: flags } : {}) };
  const parsed = contract.surveyStructureSchema.safeParse({
    ...emptySurvey,
    fields: [{ id: 'q1', code: 'Q01', type: 'short-text', label: 'Pattern', responseValidation, defaultValue: value }],
  });
  return { pattern, flags, value, success: parsed.success, issues: parsed.success ? [] : parsed.error.issues.map(compactIssue) };
})));

const imageField = (url) => ({ id: 'q1', code: 'Q01', type: 'display', label: 'Image', images: [{ url, alt: '' }] });
const urlCases = edge.urls.map((url) => {
  const parsed = contract.surveyStructureSchema.safeParse({ ...emptySurvey, fields: [imageField(url)] });
  return { url, success: parsed.success, issues: parsed.success ? [] : parsed.error.issues.map(compactIssue) };
});
const dateBoundCases = edge.dateBounds.map((bound) => {
  const parsed = contract.surveyStructureSchema.safeParse({ ...emptySurvey, fields: [{
    id: 'q1', code: 'Q01', type: 'date', dateValueType: 'date', label: 'Date', responseValidation: { dateMin: bound },
  }] });
  return { bound, success: parsed.success, issues: parsed.success ? [] : parsed.error.issues.map(compactIssue) };
});
const helpers = {
  isNumericText: edge.numericTexts.map((value) => ({ value, result: contract.isNumericText(value) })),
  numberCharacterLength: edge.numbers.map((value) => ({ value, text: String(value), result: contract.numberCharacterLength(value) })),
  isMonthDay: edge.monthDays.map((value) => ({ value, result: contract.isMonthDay(value) })),
  monthDayCount: [0, 1, 2, 4, 12, 13].map((month) => ({ month, result: contract.monthDayCount(month) })),
};
const gradingSurvey = contract.parseSurveyStructure(edge.grading.survey);
const grading = {
  score: edge.grading.answers.flatMap((answers) => edge.grading.fieldCodes.map((fieldCodes) => ({
    answers, fieldCodes, result: contract.calculateSurveyScore(gradingSurvey, answers, fieldCodes ?? undefined),
  }))),
  gradeAnswer: edge.grading.gradeAnswer.map((item) => ({
    ...item, result: contract.gradeSurveyAnswer(item.grading, item.value, item.multiple ?? false, item.selected ?? true),
  })),
};

const locales = ['es', 'es-MX', 'es_ES', 'en', 'en-US', 'fr', '', null];
const localeResolution = locales.map((locale) => ({ locale, resolved: contract.resolveSurveyDiagnosticLocale(locale) }));

const out = resolve(args.out);
mkdirSync(out, { recursive: true });
const write = (filename, value) => writeFileSync(join(out, filename), `${JSON.stringify(value, null, 2)}\n`);
// One case per line keeps large case lists reviewable without multiplying their size.
const writeLines = (filename, values) => writeFileSync(join(out, filename), `[\n${values.map((value) => JSON.stringify(value)).join(',\n')}\n]\n`);
write('validation-cases.json', {
  surveyStructureVersion: contract.SURVEY_STRUCTURE_VERSION,
  cases,
});
write('url-cases.json', urlCases);
write('date-bound-cases.json', dateBoundCases);
write('helpers.json', helpers);
write('grading.json', grading);
write('diagnostic-locales.json', localeResolution);
write('language-tags.json', languageTags);
writeLines('pattern-cases.json', patternCases);
write('widget-compatibility.json', contract.FIELD_WIDGET_COMPATIBILITY);
