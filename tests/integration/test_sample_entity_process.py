from tests.utils import ObjectGenerator, RequestGenerator, wait_until


KEY_THAT_DOES_NOT_EXIST = "00000000-0000-0000-0000-000000000000"


class TestSampleEntityProcess:
    """O fluxo assíncrono, testado de fora — como um cliente o veria.

    Este teste não sabe que existe fila, nem SQS, nem consumer. Ele manda
    uma requisição e depois fica perguntando pela outra ponta (o GET) até
    a resposta mudar. Se um dia a fila for trocada por outra coisa, este
    arquivo continua valendo sem mudar uma linha.
    """

    def test_process(self):
        sample_entity = ObjectGenerator.create_sample_entity()
        _key = sample_entity["sample_entity_key"]

        status, response = RequestGenerator.GET_sample_entity(_key)
        assert status == 200
        assert response["status"] == "pending"

        status, response = RequestGenerator.POST_sample_entity_process(_key)
        assert status == 202
        assert response["sample_entity_key"] == _key

        def status_is_success():
            _, sample_entity_now = RequestGenerator.GET_sample_entity(_key)
            return sample_entity_now["status"] == "success"

        wait_until(status_is_success, f"o status da entidade {_key} virar 'success'")

        status, response = RequestGenerator.GET_sample_entity(_key)
        assert status == 200
        assert response["sample_entity_key"] == _key
        assert response["status"] == "success"
        assert response["counter"] == 0

    def test_process_not_found(self):
        status, response = RequestGenerator.POST_sample_entity_process(KEY_THAT_DOES_NOT_EXIST)
        assert status == 404
        assert response["code"] == "QIT001001"

    def test_process_finished(self):
        sample_entity = ObjectGenerator.create_sample_entity()
        _key = sample_entity["sample_entity_key"]

        ObjectGenerator.update_sample_entity(_key, "success")

        status, response = RequestGenerator.POST_sample_entity_process(_key)
        assert status == 409
        assert response["code"] == "QIT001002"

    def test_process_twice(self):
        sample_entity = ObjectGenerator.create_sample_entity()
        _key = sample_entity["sample_entity_key"]

        status, response = RequestGenerator.POST_sample_entity_process(_key)
        assert status == 202

        def status_is_success():
            _, sample_entity_now = RequestGenerator.GET_sample_entity(_key)
            return sample_entity_now["status"] == "success"

        wait_until(status_is_success, f"o status da entidade {_key} virar 'success'")

        # Depois que o consumer terminou, o mesmo pedido é recusado na
        # hora: a regra de negócio não muda por o trabalho ter vindo da
        # fila em vez de ter vindo direto de uma requisição.
        status, response = RequestGenerator.POST_sample_entity_process(_key)
        assert status == 409
        assert response["code"] == "QIT001002"
