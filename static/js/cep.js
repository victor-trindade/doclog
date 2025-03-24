document.addEventListener('DOMContentLoaded', function () {
    const cnpjField = document.querySelector('#id_cnpj');
    const cpfField = document.querySelector('#id_cpf');
    const rgField = document.querySelector('#id_rg');
    const cepField = document.querySelector('#id_cep');
    const fundadoEmField = document.querySelector('#id_fundado_em');
    const porteField = document.querySelector('#id_porte');
    const simplesField = document.querySelector('#id_simples');
    const simeiField = document.querySelector('#id_simei');
    const razaoSocialField = document.querySelector('#id_razao_social');
    const logradouroField = document.querySelector('#id_logradouro');
    const numeroField = document.querySelector('#id_numero');
    const complementoField = document.querySelector('#id_complemento');
    const bairroField = document.querySelector('#id_bairro');
    const cidadeField = document.querySelector('#id_cidade');
    const estadoField = document.querySelector('#id_estado');
    const statusField = document.querySelector('#id_status');
    const atividadeField = document.querySelector('#id_atividade');

    // Aplica máscaras usando IMask
    if (cnpjField) {
        IMask(cnpjField, { mask: '00.000.000/0000-00' });
    }
    if (cpfField) {
        IMask(cpfField, { mask: '000.000.000-00' });
    }
    if (rgField) {
        IMask(rgField, { mask: '00.000.000-0' });
    }
    if (cepField) {
        IMask(cepField, { mask: '00.000-000' });
    }

    // Seu código de lógica para preenchimento automático do CNPJ
    const alertCnpjContainer = document.createElement('div');
    const alertAtividadeContainer = document.createElement('div');
    alertCnpjContainer.style.marginTop = '5px';
    alertCnpjContainer.style.fontSize = '13px';
    alertCnpjContainer.style.color = '#555';
    alertCnpjContainer.style.display = 'none';
    alertCnpjContainer.style.fontStyle = 'bold';

    alertAtividadeContainer.style.marginTop = '5px';
    alertAtividadeContainer.style.fontSize = '13px';
    alertAtividadeContainer.style.color = '#555';
    alertAtividadeContainer.style.display = 'none';
    alertAtividadeContainer.style.fontStyle = 'bold';

    const emoji = '⚠️ ';

    if (cnpjField) {
        cnpjField.parentNode.appendChild(alertCnpjContainer);
    }
    if (atividadeField) {
        atividadeField.parentNode.appendChild(alertAtividadeContainer);
    }

    if (cnpjField) {
        cnpjField.addEventListener('input', function () {
            const cnpjValue = cnpjField.value.replace(/[^\d]/g, ''); // Remove caracteres não numéricos

            // Limpar campos relacionados
            if (atividadeField) atividadeField.value = '';
            if (fundadoEmField) fundadoEmField.value = '';
            if (porteField) porteField.value = '';
            if (simplesField) simplesField.checked = false;
            if (simeiField) simeiField.checked = false;
            if (razaoSocialField) razaoSocialField.value = '';
            if (logradouroField) logradouroField.value = '';
            if (numeroField) numeroField.value = '';
            if (complementoField) complementoField.value = '';
            if (cepField) cepField.value = '';
            if (bairroField) bairroField.value = '';
            if (cidadeField) cidadeField.value = '';
            if (estadoField) estadoField.value = '';
            if (statusField) statusField.value = '';
            alertCnpjContainer.style.display = 'none';
            alertAtividadeContainer.style.display = 'none';

            if (cnpjValue.length === 14) {
                const url = `https://open.cnpja.com/office/${cnpjValue}`;

                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === "ERROR") {
                            alertCnpjContainer.style.display = 'block';
                            alertCnpjContainer.textContent = emoji + 'CNPJ inválido ou não encontrado';
                        } else {
                            // Preencher os campos com os dados da API
                            if (fundadoEmField) fundadoEmField.value = data.founded || '';
                            if (porteField) porteField.value = data.company.size ? data.company.size.text : '';
                            if (simplesField) simplesField.checked = data.company.simples.optant || false;
                            if (simeiField) simeiField.checked = data.company.simei.optant || false;
                            if (razaoSocialField) razaoSocialField.value = data.company.name || '';
                            if (logradouroField) logradouroField.value = data.address.street || '';
                            if (numeroField) numeroField.value = data.address.number || '';
                            if (complementoField) complementoField.value = data.address.details || '';
                            if (cepField) cepField.value = data.address.zip || '';
                            if (bairroField) bairroField.value = data.address.district || '';
                            if (cidadeField) cidadeField.value = data.address.city || '';
                            if (estadoField) estadoField.value = data.address.state || '';
                            if (statusField) statusField.value = data.status.text || '';

                            let atividadeEncontrada = null;

                            if (data.mainActivity && data.mainActivity.id === 5320202) {
                                atividadeEncontrada = data.mainActivity.text;
                            } else if (data.sideActivities && data.sideActivities.length > 0) {
                                const sideActivity = data.sideActivities.find(activity => activity.id === 5320202);
                                if (sideActivity) {
                                    atividadeEncontrada = sideActivity.text;
                                }
                            }

                            if (atividadeField) {
                                if (atividadeEncontrada) {
                                    atividadeField.value = atividadeEncontrada;
                                    alertAtividadeContainer.style.display = 'none';
                                } else {
                                    atividadeField.value = '';
                                    alertAtividadeContainer.style.display = 'block';
                                    alertAtividadeContainer.textContent = emoji + 'Não possui atividade cod: 5320202';
                                }
                            }
                        }
                    })
                    .catch(error => {
                        if (atividadeField) atividadeField.value = '';
                        alertCnpjContainer.style.display = 'block';
                        alertCnpjContainer.textContent = emoji + 'Erro ao buscar CNPJ';
                    });
            }
        });
    }
});
