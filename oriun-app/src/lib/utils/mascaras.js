/**
 * ------------------------------------------------------------
 * Arquivo: mascaras.js
 * Local: src/lib/utils/mascaras.js
 * Descrição: Conjunto de funções utilitárias para aplicar
 * máscaras de formatação em campos de entrada do sistema Oriun.
 * 
 * Objetivo: Padronizar a entrada de dados sensíveis como CPF,
 * CNPJ, telefone, CEP e inscrição estadual, garantindo
 * consistência visual e validação estrutural.
 * 
 * Uso: Importar as funções conforme necessário nas telas
 * de cadastro, login, perfil, etc.
 * 
 * Exemplo:
 * import { aplicarMascaraCPF } from '$lib/utils/mascaras.js';
 * cpf = aplicarMascaraCPF(cpf);
 * 
 * ------------------------------------------------------------
 * Funções disponíveis:
 * 
 * aplicarMascaraCPF(valor: string): string
 *   - Formata CPF no padrão 000.000.000-00
 * 
 * aplicarMascaraCNPJ(valor: string): string
 *   - Formata CNPJ no padrão 00.000.000/0000-00
 * 
 * aplicarMascaraTelefone(valor: string): string
 *   - Formata telefone com DDD no padrão (00) 00000-0000
 * 
 * aplicarMascaraCEP(valor: string): string
 *   - Formata CEP no padrão 00000-000
 * 
 * aplicarMascaraInscricaoEstadual(valor: string): string
 *   - Formata inscrição estadual no padrão 000.000.000-00
 * 
 * ------------------------------------------------------------
 * Autor: Benedito (Consiste Informática)
 * Sistema: ORIUN - Rastreabilidade Bovina
 * Data: 06/10/2025
 * ------------------------------------------------------------
 */


// src/lib/utils/mascaras.js

export function aplicarMascaraCPF(valor) {
  return valor
    .replace(/\D/g, '')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}

export function aplicarMascaraCNPJ(valor) {
  return valor
    .replace(/\D/g, '')
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2');
}

export function aplicarMascaraTelefone(valor) {
  return valor
    .replace(/\D/g, '')
    .replace(/^(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{4,5})(\d{4})$/, '$1-$2');
}

export function aplicarMascaraCEP(valor) {
  return valor
    .replace(/\D/g, '')
    .replace(/^(\d{5})(\d)/, '$1-$2');
}

export function aplicarMascaraInscricaoEstadual(valor) {
  return valor
    .replace(/\D/g, '')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}
