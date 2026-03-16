import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import tseslint from 'typescript-eslint'
import prettier from 'eslint-config-prettier'
import vueParser from 'vue-eslint-parser'

export default [
  {
    ignores: ['dist', 'node_modules'],
  },

  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...vue.configs['flat/recommended'],
  prettier,

  {
    files: ['src/**/*.{js,ts,vue}'],

    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        localStorage: 'readonly',
        alert: 'readonly',
        URL: 'readonly',
        FormData: 'readonly',
        HTMLInputElement: 'readonly',
        Event: 'readonly',
      },
    },

    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': 'warn',
      'vue/attribute-hyphenation': 'off',
      'vue/attributes-order': 'off',
      'vue/multi-word-component-names': 'off',
    },
  },
]
